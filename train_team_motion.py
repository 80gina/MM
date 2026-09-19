"""Continue fine-tuning KcELECTRA on safely mapped team_motion labels.

Raw dialogue stays local. Only aggregate metrics are written to evidence/.
"""
import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL = "GGARA02/kcelectra-korean-emotion"
REVISION = "2eaf89d8d2cbfd902b93e5ec989db2ec103806fb"
TARGET_TO_LABEL = {"화남": 0, "기쁨": 1, "두려움": 2, "놀라움": 3, "슬픔": 4}
LABEL_NAMES = ["분노", "기쁨", "불안", "당황", "슬픔", "상처"]


class EmotionDataset(Dataset):
    def __init__(self, rows, tokenizer):
        self.rows = rows
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        text, label = self.rows[index]
        encoded = self.tokenizer(text, max_length=128, truncation=True,
                                 padding="max_length", return_tensors="pt")
        return {key: value.squeeze(0) for key, value in encoded.items()} | {
            "labels": torch.tensor(label, dtype=torch.long)
        }


def split_name(path: Path) -> str:
    bucket = int(hashlib.sha1(str(path).encode("utf-8")).hexdigest()[:8], 16) % 100
    return "train" if bucket < 80 else "validation" if bucket < 90 else "test"


def reservoir_add(bucket, seen, row, limit, rng):
    seen[0] += 1
    if len(bucket) < limit:
        bucket.append(row)
    else:
        index = rng.randrange(seen[0])
        if index < limit:
            bucket[index] = row


def load_rows(root: Path, max_per_class: int, seed: int):
    rng = random.Random(seed)
    buckets = defaultdict(list)
    seen = defaultdict(lambda: [0])
    excluded = Counter()
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError):
            excluded["invalid_json"] += 1
            continue
        split = split_name(path.relative_to(root))
        for row in data.get("Conversation", []):
            text = str(row.get("Text", "")).strip()
            target = str(row.get("VerifyEmotionTarget", "")).strip()
            if not text:
                excluded["empty_text"] += 1
                continue
            if target not in TARGET_TO_LABEL:
                excluded[f"unmapped:{target or '<EMPTY>'}"] += 1
                continue
            label = TARGET_TO_LABEL[target]
            key = (split, label)
            reservoir_add(buckets[key], seen[key], (text, label), max_per_class, rng)
    result = {name: [] for name in ("train", "validation", "test")}
    for (split, _), rows in buckets.items():
        result[split].extend(rows)
    for rows in result.values():
        rng.shuffle(rows)
    return result, excluded, {f"{split}:{LABEL_NAMES[label]}": count[0] for (split, label), count in seen.items()}


def macro_f1(labels, predictions):
    scores = []
    per_class = {}
    for label in range(5):
        tp = sum(p == label and y == label for p, y in zip(predictions, labels))
        fp = sum(p == label and y != label for p, y in zip(predictions, labels))
        fn = sum(p != label and y == label for p, y in zip(predictions, labels))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[LABEL_NAMES[label]] = {"precision": precision, "recall": recall, "f1": f1}
        scores.append(f1)
    return sum(scores) / len(scores), per_class


def evaluate(model, loader, device):
    model.eval()
    labels, predictions = [], []
    total_loss = 0.0
    with torch.inference_mode():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            output = model(**batch)
            total_loss += float(output.loss.detach())
            labels.extend(batch["labels"].cpu().tolist())
            predictions.extend(output.logits.argmax(-1).cpu().tolist())
    accuracy = sum(a == b for a, b in zip(labels, predictions)) / max(1, len(labels))
    f1, per_class = macro_f1(labels, predictions)
    return {"loss": total_loss / max(1, len(loader)), "accuracy": accuracy,
            "macro_f1_5_mapped_classes": f1, "per_class": per_class, "samples": len(labels)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/kcelectra-team-motion"))
    parser.add_argument("--max-per-class", type=int, default=100)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    rows, excluded, available = load_rows(args.data_dir, args.max_per_class, args.seed)
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, revision=REVISION)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    loaders = {name: DataLoader(EmotionDataset(items, tokenizer), batch_size=args.batch_size,
                                shuffle=name == "train") for name, items in rows.items()}
    optimizer = AdamW(model.parameters(), lr=1e-5, weight_decay=0.01)
    history = []
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0
        for batch in loaders["train"]:
            optimizer.zero_grad()
            batch = {key: value.to(device) for key, value in batch.items()}
            output = model(**batch)
            output.loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += float(output.loss)
        validation = evaluate(model, loaders["validation"], device)
        history.append({"epoch": epoch + 1, "train_loss": total_loss / max(1, len(loaders["train"])),
                        "validation": validation})
        print(json.dumps(history[-1], ensure_ascii=False))
    test = evaluate(model, loaders["test"], device)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    report = {
        "base_model": MODEL, "revision": REVISION, "device": str(device),
        "mapping": {key: LABEL_NAMES[value] for key, value in TARGET_TO_LABEL.items()},
        "warning": "사랑스러움·없음은 제외했고 상처 라벨의 신규 표본은 없어 별도 보존성 평가가 필요함",
        "split_method": "JSON 파일 경로 SHA-1 기반 80/10/10 그룹 분리",
        "selected_samples": {key: len(value) for key, value in rows.items()},
        "available_mapped_samples": available, "excluded": dict(excluded),
        "epochs": args.epochs, "batch_size": args.batch_size, "max_length": 128,
        "history": history, "test": test,
    }
    Path("evidence/team-motion-training.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(test, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
