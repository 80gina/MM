---
title: Mindily
emoji: 🌿
colorFrom: purple
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: 감정 일기를 읽고 출처 있는 회복 활동을 추천하는 AI 감정 코치
---

# Mindily

감정 일기를 **실제 한국어 감정 분류 모델(KcELECTRA)**로 읽고, **출처가 있는** 회복 활동까지 연결하는 AI 감정 코치입니다.

> 코디세이 AI 네이티브 Final Project · 소스: https://github.com/80gina/MM

## 사용 방법

1. 오늘 있었던 일과 지금의 마음을 자유롭게 적습니다.
2. 스트레스 정도를 1~5로 선택하고 분석을 요청합니다.
3. 모델이 제안한 감정을 확인하고, 다르면 무드 미터에서 **직접 수정**합니다.
4. 감정에 맞는 회복 활동을 출처 링크와 함께 확인합니다.

## 이 서비스가 지키는 것

- **일기 원문은 서버에 저장되지 않습니다.** 브라우저에만 보관되며, 생성형 AI에도 전송하지 않습니다.
- 코치 문장은 **검색된 출처 카드 안에서만** 생성됩니다. 출처는 화면에 함께 표시됩니다.
- 선호 활동 기억은 **동의한 경우에만** 저장하고 **30일 후 자동 삭제**합니다.
- **의료적 진단이나 치료를 제공하지 않습니다.**
- AI가 생성한 문장에는 그 사실을 표시합니다.

## 환경 변수 (Space Settings → Variables and secrets)

| 이름 | 종류 | 설명 |
|---|---|---|
| `CODYSSEY_API_KEY` | **Secret** | 코디세이에서 발급받은 키. 없으면 규칙 기반 문장으로 자동 폴백 |
| `CODYSSEY_API_BASE` | Variable | 코디세이 엔드포인트 (예: `https://api.codyssey.kr/v1`) |
| `CODYSSEY_MODEL` | Variable | 코디세이에서 지정한 모델명 (예: `gpt-4o-mini`) |
| `MINDILY_LLM_TIMEOUT` | Variable | 기본 `20` (초). 추론형 모델은 응답이 느릴 수 있음 |

## 상태 확인

- `GET /api/health` — 모델·리비전·생성 경로 상태
- `GET /api/llm/status` — 생성형 활성 여부와 접지 정책 (키 값은 노출되지 않음)

## 알아둘 점

무료 등급 Space는 영구 디스크가 없어 **재시작 시 피드백·선호 기억 데이터가 초기화**됩니다. 사용자 테스트 후에는 집계 결과를 바로 내려받아 보관하세요.
