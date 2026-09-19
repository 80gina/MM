# 시스템 아키텍처

![Mindily 시스템 아키텍처](architecture.svg)

---

## 1. 계층 구조

| 계층 | 구성 | 책임 |
|---|---|---|
| ① 사용자 | 모바일·데스크톱 브라우저 | 설치 없이 HTTPS URL로 접속 |
| ② 프론트엔드 | `dist/index.html`, `app.js`, `styles.css`, localStorage | 화면 렌더링, API 호출, **일기 원문 기기 보관** |
| ③ API | `server.py` (FastAPI + Uvicorn) | 요청 검증, 라우팅, 상태 공개 |
| ④ Agent | `coach_agent.py` | 의도 판별 후 도구를 순서대로 호출 |
| ⑤ 모델·지식·저장 | KcELECTRA, `llm.py`, `rag.py`, `healing_knowledge.py`, `memory_db.py`, `feedback_db.py` | 분류 추론, 출처 접지 생성, 동의 기반 저장 |
| ⑥ 배포 | Dockerfile → Hugging Face Spaces, GitHub `main` | 영구 HTTPS URL 제공, 이력 관리 |

---

## 2. 핵심 데이터 흐름

### 2.1 감정 일기 흐름

```
사용자 일기 입력 + 스트레스 1~5
  → POST /api/agent/coach
  → coach_agent: 의도 = "일기"
      ├─ analyze_emotion(text, stress)
      │     → KcELECTRA 추론 → 6개 감정 점수 → 무드 미터 좌표
      ├─ retrieve_grounding(emotion, stress)
      │     → healing_knowledge 검색 → 출처 카드 3장
      ├─ generate_coach_message(emotion, stress, sources)   ← 생성형 AI
      │     → 출처 카드만 컨텍스트로 전달 (일기 원문 미전송)
      │     → 안전 검사 통과 시 채택, 실패 시 규칙 기반 폴백
      └─ recommend_healing(emotion, stress, 선호)
            → 출처 링크가 붙은 추천 카드
  → 응답: 코치 문장 + 출처 + 추천 카드 + generation 경로 + 도구 실행 추적
  → 사용자가 무드 미터에서 최종 감정 확정 (모델 제안과 별도 필드)
  → localStorage에 원문·확정 감정 저장 (서버 미전송)
```

### 2.2 생성형 AI 경로 상세

```
                     ┌─ 키 미설정  → deterministic_fallback (not_configured)
generate_coach_message ┼─ 호출 실패  → deterministic_fallback (call_failed)
                     ├─ 금지어 검출 → deterministic_fallback (safety_filter)
                     └─ 정상        → llm_grounded
```

어느 경로든 **같은 출처 카드**를 함께 반환하므로, 사용자는 "왜 이 활동을 권했는가"를 언제나 링크로 확인할 수 있습니다.

### 2.3 기억·피드백 흐름

```
[동의 O] 선호 활동 → POST /api/memory → SQLite 저장 (30일 만료)
[동의 X] 저장하지 않음 — 기능은 그대로 사용 가능
종료 설문 만족도 1~5 → save_user_feedback → 익명 집계 SQLite
다음 방문 → POST /api/memory/read → 30일 이내 선호만 추천 가중치에 반영
```

---

## 3. 설계 결정과 근거

| 결정 | 대안 | 선택 이유 |
|---|---|---|
| 감정 **분류**에 전용 모델 | LLM에게 감정 추정 요청 | 점수·모델 버전을 공개해 **검증 가능**. LLM 추정은 근거 제시 불가 |
| 감정 **표현**에 생성형 AI | 규칙 기반 템플릿만 사용 | 문장의 자연스러움은 생성형이 우위. 단, 출처 밖으로 나가지 못하게 제한 |
| LLM에 **일기 원문 미전송** | 원문 전달로 공감도 향상 | 감정 일기는 가장 민감한 기록. 유출 경로 자체를 제거 |
| 생성 실패 시 **자동 폴백** | 오류 표시 | 외부 API 장애가 서비스 중단이 되지 않게. 경로는 항상 공개 |
| 일기 원문 **브라우저 보관** | 서버 DB 저장 | 개인정보 최소 수집 |
| 선호 기억 **30일 만료** | 무기한 보관 | 개인화와 보호를 동시에 증명 |
| **Hugging Face Spaces** 배포 | Render 유료 플랜 | 무료 등급으로 영구 HTTPS URL, 모델을 이미지에 동봉해 콜드스타트 제거 |

---

## 4. 개인정보 경계

다이어그램에서 **일기 원문은 ② 계층을 벗어나지 않습니다.**

| 데이터 | 저장 위치 | 보존 | 동의 | 외부 전송 |
|---|---|---|---|---|
| 일기 원문 | 브라우저 localStorage | 사용자 삭제 시까지 | 불필요 | **없음 (LLM에도 미전송)** |
| 확정 감정·스트레스 | 브라우저 localStorage | 동일 | 불필요 | 없음 |
| 선호 활동 | 서버 SQLite | 30일 자동 정리 | **필수** | 없음 |
| 만족도·의견 | 서버 SQLite (익명) | 과제 종료 시 파기 | **필수** | 없음 |

생성형 AI에 전달되는 것은 **감정 라벨 · 스트레스 숫자 · 출처 카드 3장**뿐이며, 이는 `test_llm.py`의 `prompt_excludes_diary_text` 검사로 확인합니다.
Agent 실행 추적에도 **도구 이름만** 기록합니다.

---

## 5. 배포 구성 (Hugging Face Spaces)

| 항목 | 값 |
|---|---|
| SDK | Docker |
| 포트 | 7860 (`app_port`) |
| 하드웨어 | CPU basic (무료) |
| 모델 캐시 | **빌드 시 이미지에 동봉** — 첫 요청 콜드스타트 제거 |
| 비밀값 | `CODYSSEY_API_KEY` (Space Secrets) + `CODYSSEY_API_BASE` · `CODYSSEY_MODEL` |
| 상태 확인 | `GET /api/health`, `GET /api/llm/status` |
| 제약 | 무료 등급은 영구 디스크 없음 → 재시작 시 SQLite 초기화 |

---

## 6. 검증 증거 매핑

| 계층 | 검증 파일 |
|---|---|
| ③ API | `test_api.py`, `evidence/api-check.json` |
| ④ Agent | `test_agent.py`, `evidence/agent-check.json` |
| ⑤ RAG | `test_rag.py`, `evidence/rag-check.json` |
| ⑤ **생성형 AI** | `test_llm.py`, `evidence/llm-check.json` |
| ⑤ Memory | `test_memory_restart.py`, `evidence/memory-retention-check.json` |
| ⑤ Feedback | `test_feedback.py` |
| ⑥ 패키징 | `test_packaging.py` |

---

## 7. Mermaid 버전 (발표 슬라이드용)

```mermaid
flowchart TD
    U["사용자<br/>모바일 브라우저"] --> FE["프론트엔드 dist/"]
    FE -.일기 원문 기기 보관.-> LS[("localStorage")]
    FE --> API["FastAPI server.py"]
    API --> AG["coach_agent.py<br/>의도 판별"]
    AG --> T1["analyze_emotion"]
    AG --> T2["retrieve_grounding"]
    AG --> T3["generate_coach_message<br/>생성형 AI"]
    AG --> T4["recommend_healing"]
    AG --> T5["save_user_feedback"]
    T1 --> M[("KcELECTRA<br/>감정 분류")]
    T2 --> R[("RAG 지식베이스<br/>출처·라이선스")]
    T3 --> R
    T3 --> G[("코디세이 생성형 API<br/>출처 안에서만 생성")]
    T4 --> MEM[("Long-term Memory<br/>동의·30일")]
    T5 --> FB[("피드백 SQLite<br/>익명 집계")]
```
