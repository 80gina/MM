"""Aggregate local emotion labels without exposing dialogue text."""
import argparse
import json
from collections import Counter
from pathlib import Path

FIELDS = (
    "VerifyEmotionCategory", "SpeakerEmotionCategory",
    "VerifyEmotionObject", "SpeakerEmotionObject",
    "VerifyEmotionLevel", "SpeakerEmotionLevel",
    "VerifyEmotionTarget", "SpeakerEmotionTarget",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("evidence/training-data-audit.json"))
    args = parser.parse_args()
    counts = {field: Counter() for field in FIELDS}
    files = list(args.data_dir.rglob("*.json"))
    conversations = utterances = empty_text = invalid_json = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError):
            invalid_json += 1
            continue
        rows = data.get("Conversation", []) if isinstance(data, dict) else []
        conversations += bool(rows)
        for row in rows:
            if not isinstance(row, dict):
                continue
            utterances += 1
            empty_text += not bool(str(row.get("Text", "")).strip())
            for field in FIELDS:
                value = str(row.get(field, "")).strip() or "<EMPTY>"
                counts[field][value] += 1
    result = {
        "data_dir_name": args.data_dir.name,
        "json_files": len(files),
        "valid_conversation_files": conversations,
        "utterances": utterances,
        "empty_text": empty_text,
        "invalid_json": invalid_json,
        "field_counts": {field: dict(counter.most_common()) for field, counter in counts.items()},
        "privacy": "대화 원문과 화자 개인정보를 출력하지 않은 집계 결과",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "field_counts"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
