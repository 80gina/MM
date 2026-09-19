# Hugging Face Space 배포 가이드

기존 Render 설정은 유료 플랜(1c-2g + 2GB 디스크)을 전제로 해 막혀 있었습니다. **무료 등급으로 영구 HTTPS URL을 얻을 수 있는 Hugging Face Spaces**로 전환했습니다.

| 항목 | 값 |
|---|---|
| SDK | Docker |
| 포트 | 7860 |
| 하드웨어 | CPU basic (무료) |
| URL 형식 | `https://yellowmug-mindily.hf.space` |
| 모델 캐시 | 빌드 시 이미지에 동봉 → 첫 요청 지연 없음 |

---

## 1. Space 만들기 (최초 1회)

1. https://huggingface.co/new-space 접속
2. 설정
   - **Space name**: `mindily`
   - **License**: MIT
   - **SDK**: **Docker** → *Blank*
   - **Hardware**: CPU basic (무료)
   - **Visibility**: Public
3. **Create Space**

## 2. 생성형 AI 키 등록

Space 페이지 → **Settings** → *Variables and secrets*

| 이름 | 종류 | 값 |
|---|---|---|
| `CODYSSEY_API_KEY` | **Secret** | 코디세이에서 발급받은 API 키 |
| `CODYSSEY_API_BASE` | Variable | 코디세이 엔드포인트 (예: `https://api.codyssey.kr/v1`) |
| `CODYSSEY_MODEL` | Variable | 코디세이에서 지정한 모델명 (예: `gpt-4o-mini`) |

> 세 값은 코디세이에서 안내받은 것을 그대로 넣습니다. OpenAI 호환 규격이므로 다른 공급자로 바꿀 때도 이 세 값만 교체하면 됩니다.
> 키를 등록하지 않아도 서비스는 동작합니다. 코치 문장이 규칙 기반으로 폴백되고, `/api/llm/status`가 `mode: deterministic_fallback`을 반환합니다.

## 3. 배포

```bash
# 최초 1회: HF 로그인
pip install huggingface_hub
huggingface-cli login

# 배포
chmod +x deploy_space.sh
./deploy_space.sh yellowmug
```

스크립트가 하는 일:
1. Space 저장소를 임시 폴더로 clone
2. 배포에 필요한 파일만 복사 (`Dockerfile`, `requirements.txt`, `*.py`, `dist/`)
3. `SPACE_README.md`를 Space용 `README.md`로 복사 — **Space는 YAML 프런트매터가 필요**하기 때문
4. 커밋 후 push → Space에서 빌드 자동 시작

최초 빌드는 약 **10~15분**(PyTorch 설치 + 모델 다운로드)이 걸립니다. Space 페이지의 **Logs** 탭에서 진행 상황을 볼 수 있습니다.

## 4. 배포 확인

```bash
curl https://yellowmug-mindily.hf.space/api/health
curl https://yellowmug-mindily.hf.space/api/llm/status
```

기대 결과:

```json
{
  "status": "ready",
  "model": "GGARA02/kcelectra-korean-emotion",
  "revision": "2eaf89d8d2cbfd902b93e5ec989db2ec103806fb",
  "generation": {
    "llm_enabled": true,
    "provider": "codyssey (OpenAI-compatible)",
    "mode": "llm_grounded",
    "sends_diary_text": false
  }
}
```

휴대폰에서 URL을 열어 실제 분석까지 확인하고, 화면을 캡처해 `evidence/`에 저장합니다.

---

## 알아둘 점

### 데이터가 영구 저장되지 않습니다
무료 등급 Space는 영구 디스크가 없어 **재시작(코드 푸시·장시간 미사용 후 재개)하면 SQLite가 초기화**됩니다.

사용자 테스트 직후 반드시 집계를 내려받으세요.

```bash
# Space의 Files 탭에서는 런타임 생성 파일을 볼 수 없으므로,
# 테스트 종료 직후 아래 엔드포인트나 로컬 재현으로 집계를 확보한다.
python feedback_summary.py > evidence/user-test-summary.txt
git add evidence/user-test-summary.txt && git commit -m "Add user test summary"
```

필요하면 Space Settings에서 **Persistent Storage**(유료)를 켜고 `MINDILY_FEEDBACK_DB` / `MINDILY_MEMORY_DB`를 `/data/` 아래로 바꾸면 됩니다.

### 절전 모드
무료 Space는 48시간 미사용 시 절전합니다. 발표·테스트 **10분 전에 URL을 한 번 열어** 깨워 두세요.

### 삭제한 파일
| 파일 | 이유 |
|---|---|
| `render.yaml` | 유료 플랜 전제, HF Spaces로 대체 |
| `START_QUICK_TUNNEL.cmd`, `docs/QUICK_TUNNEL.md` | 임시 터널은 영구 URL 확보로 불필요 |
| `.openai/hosting.json` | 정적 호스팅 설정, 현재 구조와 무관 |
