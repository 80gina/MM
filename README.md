# Mindily 🌿

> **감정을 기록에서 끝내지 않는 AI 감정 코치**
> 코디세이 AI 네이티브 Final Project · 팀 3인

| | |
|---|---|
| 🌐 **서비스 열기** | **https://yellowmug-mindily.hf.space** · [Space 관리](https://huggingface.co/spaces/yellowmug/mindily) |
| 📄 **결과보고서** | [docs/결과보고서.md](docs/결과보고서.md) |
| 📊 **발표자료** | [docs/presentation.pdf](docs/presentation.pdf) · [편집용 .pptx](docs/presentation.pptx) |
| 🎬 **시연 영상** | [docs/mindily-demo-3min.mp4](docs/mindily-demo-3min.mp4) · 3분 01초 (대본: [시연영상대본](docs/시연영상대본.md)) |

---

## 무엇을 만들었나

일기를 쓰면 **실제 한국어 감정 분류 모델**이 감정을 읽고, **생성형 AI가 검색된 출처 안에서만** 코치 문장을 만들어, 근거가 있는 회복 활동까지 연결합니다.

```
일기 작성 → 감정 분석(KcELECTRA) → 무드 미터에서 직접 수정
        → 출처 접지 코치 문장(생성형 AI) + 명언·꽃·향
        → 활동을 앱 안에서 바로 실행 (자연의 소리는 브라우저가 합성)
        → 기록 누적 → 주·월·연 흐름과 감정 분석 보고서
        → 만족도 → (동의 시) 30일 선호 기억
```

**화면 넷**

| 화면 | 하는 일 |
|---|---|
| 감정 일기 | 한 문장 쓰고 스트레스 기록 → 분석 |
| AI 감정 분석 | 6개 감정 레이더 · 저작권 만료 인용구 · 추천 꽃과 향 · 무드 미터 |
| 맞춤형 힐링 코치 | 활동을 골라 **앱 안에서** 5단계 안내대로 실행. 빗소리·바람·파도 재생 |
| 마음 기록 | 주간·월간·연간 스트레스 흐름과 감정 분석 보고서 (텍스트로 저장) |

사용자는 홈·데스크톱 안내 문구를 직접 바꿀 수 있습니다. 감정 정리 화면에서는 최신 일기의 사건·마음 초안을 만들고 수정할 수 있으며, ‘지금 무엇이 필요할까요?’ 아래의 예시 5개를 선택해 입력할 수 있습니다. 마음 기록에서는 주간·월간·연간을 고른 뒤 주요 사건 팝업에서 같은 사건으로 보이는 기록을 한 카드에 묶어 `경과 요약 → 감정 변화 → 날짜별 근거` 보고서 형식으로 확인합니다. 예를 들어 “친구와 싸움: 10월 1일 의견 차이로 화남 → 10월 2일 대화 후 안도”처럼 표시됩니다. 사건 제목·경과를 수정하거나 잘못 묶인 기록을 분리하고, 목록을 브라우저에 저장·삭제할 수 있습니다. 저장한 목록은 보고서 텍스트 파일에도 포함됩니다.

초안 기능은 전송 안내에 동의하고 버튼을 눌렀을 때만 실행됩니다. AI 연결이 없는 환경에서는 일기 문장을 발췌한 임시 초안을 보여줍니다. [초안 기능 검증 기록](evidence/diary-draft-check.json)을 참고하세요.

### 설계의 핵심은 **역할 분리**입니다

| | 맡은 AI | 이유 |
|---|---|---|
| 감정 **판정** | 전용 분류 모델 (KcELECTRA) | 점수와 모델 버전을 공개할 수 있어 **검증 가능** |
| 감정 **표현** | 생성형 AI (코디세이 제공 API) | 공감 문장의 자연스러움. 단 **출처 밖으로 나가지 못하게** 제한 |

---

## 필수 기술 요소 — 요구 2개, 구현 4개

| 요소 | 구현 | 검증 |
|---|---|---|
| **AI Agent** | `coach_agent.py` — 의도 판별 후 도구 순차 호출 | [`agent-check.json`](evidence/agent-check.json) |
| **RAG** | `rag.py` · `healing_knowledge.py` — 근거 검색·출처 부착 | [`rag-check.json`](evidence/rag-check.json) |
| **생성형 AI** | `llm.py` — 출처 접지 생성, 안전 필터, 자동 폴백 | [`llm-check.json`](evidence/llm-check.json) |
| **Long-term Memory** | `memory_db.py` — 동의 저장, 30일 만료·삭제 | [`memory-retention-check.json`](evidence/memory-retention-check.json) |

---

## 모델 적용 결과 (실측)

| 입력 | 최상위 감정 | 점수 | 청크 | 측정 위치 |
|---|---|---|---|---|
| `내일 발표를 잘할 수 있을지 걱정돼요.` | **불안** | **0.980** | 1 | **배포 서버 실측** |
| 같은 문장 | 불안 | 0.941 | 1 | 로컬 (`evidence/api-check.json`) |
| 긴 글 (128토큰 초과) | 불안 | 0.437 | **2** | 로컬 |

로컬 `team_motion` 폴더에는 AI Hub의 [감정이 태깅된 자유대화 (성인)](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=&currMenu=&dataSetSn=71631&topMenu=)과 [감정이 태깅된 자유대화 (청소년)](https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&currMenu=115&dataSetSn=71632&pageIndex=11&srchDetailCnd=DETAILCND001&srchOptnCnd=OPTNCND001&srchOrder=ORDER001&srchPagePer=20&topMenu=100) 자료가 있습니다. 로컬 파일에서 집계한 발화 847,156건 중 학습·검증·테스트 각 100건으로 추가 학습을 시험했으나 테스트 정확도 **0.26**(무작위 기대값 0.20)에 그쳐 **채택하지 않고 공개 모델을 유지**했습니다. 공개 모델의 원 학습 자료는 AI Hub의 별도 데이터셋인 **감성대화말뭉치**입니다. 판단 근거와 전체 수치는 [모델 적용 결과](docs/모델적용결과.md)에 있습니다.

---

## 시스템 아키텍처

![시스템 아키텍처](docs/architecture.svg)

설계 근거는 [아키텍처 문서](docs/architecture.md)에 정리했습니다.

---

## 생성형 AI를 안전하게 쓰는 방법

생성형 AI가 자유롭게 답하면 없는 활동이나 의료적 조언을 만들어냅니다. **세 겹으로** 막았습니다.

| 층 | 방법 |
|---|---|
| 입력 | 일반 코치 문장에는 검색된 출처 카드 3장만 전달. **일기 원문은 보내지 않음**. 정리·보고서 초안은 별도 동의 후에만 원문을 사용 |
| 지시 | 카드 밖 활동 생성 금지 · 진단/처방/병원 권유 금지 · 감정 단정 금지 |
| 출력 | 금지어 검출 시 문장을 폐기하고 규칙 기반으로 폴백 |

모든 응답은 어느 경로로 만들어졌는지 스스로 밝힙니다.

| `generation` | 의미 |
|---|---|
| `llm_grounded` | 생성형 AI가 출처 안에서 작성 |
| `deterministic_fallback` | 규칙 기반 문장 (사유: `not_configured` / `call_failed` / `safety_filter`) |

확인: `GET /api/llm/status` — 활성 여부, 접지 정책, 마지막 실패 사유(`last_error`)를 공개합니다. API 키는 어떤 응답에도 포함하지 않습니다.

배포 서버 실측 (2026-09-21):

```
generation: llm_grounded   ·  11.9초  ·  모델 gpt-5-mini (코디세이 제공)
"지금 조금 불안하게 느껴지실 수 있어요. 편안한 자세에서 무리하지 않고
 천천히 숨을 들이쉬고 내쉬는 1분 호흡하기를 해보세요."
```

감정을 단정하지 않고, 검색된 카드에 있는 활동만 언급합니다.

---

## 앱으로 설치하기

주소를 열고 **홈 화면에 추가**하면 앱스토어 없이 아이콘이 생기고, 주소창 없는 전체 화면으로 열립니다.

| 기기 | 방법 |
|---|---|
| 안드로이드 · Chrome | 하단 설치 안내 → **설치** |
| 아이폰 · Safari | 공유(↑) → **홈 화면에 추가** |
| PC · Chrome/Edge | 주소창 오른쪽 설치 아이콘 |

서비스 워커는 **화면 자원(HTML·CSS·JS·아이콘)만** 캐시합니다. `/api/*` 응답은 캐시하지 않으므로
감정 분석 결과가 오래된 값으로 보이는 일이 없고, 일기 내용이 캐시에 남지도 않습니다.
오프라인에서는 화면이 열리고 일기 작성은 가능하지만, 분석은 연결된 뒤에 수행됩니다.

---

## 개인정보 처리

| 데이터 | 저장 위치 | 보존 | 동의 | 외부 전송 |
|---|---|---|---|---|
| 일기 원문 | 브라우저 localStorage | 사용자 삭제 시까지 | 분석 요청 시 서버 전송; 초안 생성은 별도 동의 | 분석 서버에는 저장하지 않음. 정리·보고서 초안을 요청하고 동의한 경우에만 설정된 외부 AI로 전송 |
| 기록 그래프·보고서 | 브라우저 localStorage | 최근 400건 | 사건 초안 생성은 별도 동의 | 수치·그래프는 기기 안에서 계산. 선택 기간의 일기를 10건씩 나누어 초안을 요청하며, 서버에 저장하지 않음 |
| 개인 문구·수정한 초안 | 브라우저 localStorage | 사용자 삭제 시까지 | 불필요 | 저장 후 외부 전송 없음 |
| 선호 활동 | 서버 SQLite | 30일 자동 삭제 | **필수** | 없음 |
| 만족도·의견 | 서버 SQLite (익명) | 과제 종료 시 파기 | **필수** | 없음 |

- AI가 생성·추천한 콘텐츠임을 화면에 표시합니다.
- 동의를 거부해도 핵심 기능을 그대로 사용할 수 있습니다.
- 의료적 진단이나 치료를 제공하지 않습니다.

---

## 팀원 및 역할

| 이름 | 역할 | 담당 | 대표 커밋 |
|---|---|---|---|
| **김다빈** | 기획 / UX | 콘셉트, 모바일 UI, 접근성, 사용자 테스트 설계 | [`7689aba`](https://github.com/80gina/MM/commit/7689aba) · [`f164d49`](https://github.com/80gina/MM/commit/f164d49) · [`1148bb4`](https://github.com/80gina/MM/commit/1148bb4) |
| **김진아** | 개발 | 모델 연동, FastAPI, Agent·RAG·생성형 AI·Memory, 배포 | [`4c58d82`](https://github.com/80gina/MM/commit/4c58d82) · [`6ea3d1c`](https://github.com/80gina/MM/commit/6ea3d1c) · [`b77aea5`](https://github.com/80gina/MM/commit/b77aea5) |
| **이승민** | 검증 / 문서 | 기능명세, 테스트, 사용자 5명 피드백 수집·정리 | [`e547f92`](https://github.com/80gina/MM/commit/e547f92) · [`557d1b0`](https://github.com/80gina/MM/commit/557d1b0) · [`30d6917`](https://github.com/80gina/MM/commit/30d6917) |

---

## 기술 스택

| 영역 | 선택 |
|---|---|
| 감정 분류 | KcELECTRA (`GGARA02/kcelectra-korean-emotion`, 리비전 `2eaf89d8` 고정) |
| 생성형 AI | 코디세이 제공 API (OpenAI 호환, `gpt-5-mini`) — 모델 계열별 요청 규격 자동 대응 |
| 백엔드 | FastAPI · Uvicorn · PyTorch (CPU) |
| 프론트엔드 | HTML · CSS · JavaScript (빌드 체인 없음) |
| 앱 형태 | 설치형 웹앱(PWA) — manifest + 서비스 워커, 홈 화면 설치·오프라인 화면 |
| 저장 | 브라우저 localStorage + SQLite |
| 배포 | Docker → Hugging Face Spaces (`yellowmug/mindily`) |

선정 이유는 [기획서 5장](docs/기획서.md)에 정리했습니다.

---

## 실행 방법

### 로컬 실행
```bash
git clone https://github.com/80gina/MM.git
cd MM
pip install -r requirements.txt
export CODYSSEY_API_KEY=...                       # 생략 시 규칙 기반 문장으로 동작
export CODYSSEY_API_BASE=https://.../v1           # 코디세이에서 받은 엔드포인트
export CODYSSEY_MODEL=gpt-4o-mini                 # 코디세이에서 지정한 모델명
python -m uvicorn server:app --host 127.0.0.1 --port 8010
# http://127.0.0.1:8010
```

### Hugging Face Space 배포

Windows에서는 저장소 루트의 스크립트를 더블클릭합니다. 바뀐 파일만 올리고 필요 없어진 파일은 지웁니다.

```
push_to_huggingface.cmd
```

로그인은 계정 비밀번호가 아니라 Hugging Face **쓰기(write) 토큰**을 씁니다.
macOS·Linux에서는 `./deploy_space.sh yellowmug` 를 쓸 수 있습니다.
Space Settings → *Variables and secrets* 에 `CODYSSEY_API_KEY`(Secret), `CODYSSEY_API_BASE`, `CODYSSEY_MODEL`을 등록합니다.
자세한 절차는 [배포 가이드](docs/DEPLOY_HF.md)를 참고하세요.

### 상태 확인
```bash
curl https://yellowmug-mindily.hf.space/api/health
curl https://yellowmug-mindily.hf.space/api/llm/status
```

---

## 사용자 테스트 결과

| 항목 | 결과 |
|---|---|
| 참여자 | (테스트 후 기입) |
| 분석 이해도 / 공감도 / 추천 유용성 / 접근성 | (테스트 후 기입) |
| 사용자 피드백으로 수정한 항목 | (테스트 후 기입) |
| 자체 점검으로 수정한 항목 | **8건** — [피드백 기록](docs/피드백기록.md) (사용자 응답과 별도로 집계) |

개선 전후 비교는 [피드백 기록](docs/피드백기록.md)에 있습니다.

---

<details>
<summary><b>📁 전체 문서 목록</b></summary>

### 제출 문서
- [기획서](docs/기획서.md) — 문제 정의·타겟·AI 활용·기술 접근·일정
- [결과보고서](docs/결과보고서.md) — 평가 항목별 구현 결과
- [기능명세서](docs/기능명세서.md) — 기능·비기능 요구사항
- [시스템 아키텍처](docs/architecture.md) — 계층 구조와 설계 근거
- [발표자료 구성안](docs/발표자료구성안.md) · [시연계획서](docs/시연계획서.md)
- [팀 역할 및 기여 기록](docs/TEAM_ROLES.md)

### 기록·분석
- [모델 적용 결과](docs/모델적용결과.md) — 실제 분류 결과·추가 학습 측정값·채택 판단
- [모델학습보고서](docs/모델학습보고서.md) — 전처리·토큰화·학습 설정 상세
- [프로그램 비평 및 향후 방향](docs/프로그램비평.md)
- [미션수행체크리스트](docs/미션수행체크리스트.md) · [제출증빙자료](docs/제출증빙자료.md)

### 검증 증거
- [API](evidence/api-check.json) · [Agent](evidence/agent-check.json) · [RAG](evidence/rag-check.json) · [생성형 AI](evidence/llm-check.json)
- [배포 환경 실측](evidence/deploy-check.json) — 상태·생성 경로·실제 응답 문장·도구 추적
- [선호 기억 유지·만료](evidence/memory-retention-check.json) · [확장 추천 카드](evidence/extension-recommendations-check.json)
- [학습 데이터 전수 통계](evidence/training-data-audit.json) · [파일럿 추가 학습](evidence/team-motion-training.json)

### 운영 안내
- [배포 가이드](docs/DEPLOY_HF.md) · [실행 가이드](docs/RUN.md)
- [사용자 테스트 진행 안내](docs/사용자테스트진행안내.md) · [테스트 기록지](docs/사용자테스트기록지.md)

</details>

---

## 현재 한계

- 생성형 응답이 감정 라벨·출처 카드만 참조하므로 개별 상황 묘사의 구체성은 낮습니다.
- 추론형 모델을 쓰고 있어 코치 문장 생성에 약 12초가 걸립니다.
- 무료 Space는 영구 디스크가 없어 재시작 시 피드백·선호 데이터가 초기화됩니다. 일기와 기록 그래프는 기기 안에 있어 영향받지 않습니다.
- 기록이 기기별로 분리됩니다. 폰과 PC의 그래프는 서로 다릅니다.
- 위치 기반 추천(러닝 코스·근처 장소)은 권한·지도 API 검토 후 2단계입니다.
- 초기에 Hugging Face 측 CPU 쿼터 오류로 기동이 막혀, 그동안 임시 HTTPS 경로로 시연·테스트했습니다. 현재는 해제되어 위 주소가 상시 동작합니다.

## 출처

- 감정 분류 모델: [GGARA02/kcelectra-korean-emotion](https://huggingface.co/GGARA02/kcelectra-korean-emotion)
- 활동 카드 출처: NHS · WHO · RHS · Project Gutenberg (각 카드에 링크 표시)
- 필사·음악 콘텐츠는 저작권 만료 또는 공개 라이선스 자료만 사용합니다.
