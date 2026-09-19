"""모델 적용 결과를 실제로 측정해 evidence/model-application-check.json 으로 저장한다.

서버를 띄우지 않고 server.py와 동일한 추론 경로(128토큰 청크 + 토큰 가중 평균)를
그대로 재현하므로, 결과가 실제 서비스 동작과 일치한다.

사용법:
    python model_report.py
    git add evidence/model-application-check.json && git commit -m "Add model application results"
"""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('HF_HUB_DISABLE_TELEMETRY', '1')
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL = os.getenv('MINDILY_MODEL_PATH', 'GGARA02/kcelectra-korean-emotion')
REVISION = '2eaf89d8d2cbfd902b93e5ec989db2ec103806fb'
OUT = Path(__file__).resolve().parent / 'evidence' / 'model-application-check.json'

# 감정별 대표 문장 1개씩 + 감정 라벨이 애매한 중립 문장 1개.
# 기대 라벨은 '정답'이 아니라 사람이 붙인 참고값이며, 불일치도 그대로 기록한다.
CASES = [
    ('내일 발표를 잘할 수 있을지 걱정돼요.', '불안'),
    ('오늘 친구를 오랜만에 만나서 정말 즐거웠어요.', '기쁨'),
    ('아무것도 하기 싫고 자꾸 눈물이 나요.', '슬픔'),
    ('약속을 또 어겨서 정말 화가 나요.', '분노'),
    ('믿었던 사람한테 무시당해서 마음이 아파요.', '상처'),
    ('갑자기 이런 일이 생길 줄 몰라서 너무 당황스러워요.', '당황'),
    ('내일 비가 온다고 해서 우산을 챙겼어요.', '(중립 — 참고 라벨 없음)'),
]


def infer(tokenizer, model, text):
    encoded = tokenizer(text, truncation=True, max_length=128,
                        return_overflowing_tokens=True, padding=True, return_tensors='pt')
    encoded.pop('overflow_to_sample_mapping', None)
    started = time.time()
    with torch.inference_mode():
        chunk_scores = model(**encoded).logits.softmax(-1)
    weights = (encoded['attention_mask'].sum(-1) - 2).clamp(min=1)
    scores = (chunk_scores * weights[:, None]).sum(0) / weights.sum()
    ranked = sorted(((model.config.id2label[i], float(v)) for i, v in enumerate(scores)),
                    key=lambda x: -x[1])
    return ranked, int(chunk_scores.shape[0]), int((time.time() - started) * 1000)


def main():
    started = time.time()
    tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL, revision=REVISION, use_safetensors=True).eval()
    load_seconds = round(time.time() - started, 1)

    report = {
        'executed_at': datetime.now(timezone.utc).isoformat(),
        'model': MODEL,
        'revision': REVISION,
        'labels': list(model.config.id2label.values()),
        'inference': 'chunk 128 tokens + token-weighted mean (server.py와 동일)',
        'model_load_seconds': load_seconds,
        'scope': '합성 문장 기반 동작 확인. 실사용자 응답이나 정확도 벤치마크가 아님',
        'cases': [],
    }

    matched = 0
    for text, expected in CASES:
        ranked, chunks, latency = infer(tokenizer, model, text)
        top_name, top_score = ranked[0]
        if expected in report['labels'] and top_name == expected:
            matched += 1
        report['cases'].append({
            'text': text,
            'reference_label': expected,
            'top1': top_name,
            'top1_score': round(top_score, 4),
            'top3': [{'name': n, 'score': round(v, 4)} for n, v in ranked[:3]],
            'chunks': chunks,
            'latency_ms': latency,
            'matches_reference': (top_name == expected) if expected in report['labels'] else None,
        })

    labelled = sum(1 for _, e in CASES if e in report['labels'])
    report['reference_match'] = f'{matched}/{labelled}'

    long_text = '오늘은 정말 긴 하루였어요. ' * 40
    ranked, chunks, latency = infer(tokenizer, model, long_text)
    report['long_text_check'] = {
        'chars': len(long_text), 'chunks': chunks, 'latency_ms': latency,
        'top1': ranked[0][0], 'top1_score': round(ranked[0][1], 4),
        'note': '128토큰을 넘는 입력이 잘리지 않고 여러 청크로 나뉘어 집계되는지 확인',
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f'\n저장 완료: {OUT}')


if __name__ == '__main__':
    main()
