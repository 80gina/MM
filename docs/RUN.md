# 실행과 배포 안내

Python 3.12 기준. 저장소 폴더에서 실행합니다.
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000 --no-access-log
```
http://127.0.0.1:8000 을 엽니다. 설치 후에는 START.cmd를 두 번 클릭합니다. 처음에는 모델 다운로드 시간이 필요합니다.
`MINDILY_OFFLINE=1`은 지정한 `HF_HOME` 캐시에 토크나이저와 모델 가중치가 모두 있을 때만 사용합니다. 캐시가 일부만 있을 때는 서버 시작이 실패하므로 처음 실행에서는 설정하지 마세요.
dist/index.html만 직접 열면 실제 분석 API를 사용할 수 없습니다.

일반 사용자는 배포 후 URL만 열면 되도록 구성합니다. 무료 Cloudflare Quick Tunnel에서 임시 외부 HTTPS 접속은 검증했지만 상시 호스팅은 아직 하지 않았습니다.
Dockerfile과 `render.yaml`은 배포 준비용이며 빌드·배포 성공 증빙이 아닙니다. 만족도와 동의한 선호 활동은 SQLite 파일로 `data/`에 저장되므로 배포 때 영속 볼륨이 필요합니다.
`python test_packaging.py`는 Dockerfile에 서버가 import하는 로컬 모듈이 모두 포함됐는지 검사합니다. 실제 Docker 이미지 빌드는 Docker가 설치된 환경에서 별도로 확인해야 합니다.
```sh
docker build -t mindily .
docker run --rm -p 8000:8000 -v mindily-data:/app/data mindily
```
모델 다운로드 공간·메모리·HTTPS·요청 제한·로그 정책을 확인한 뒤 배포합니다. GitHub Pages만으로 Python 모델을 실행할 수 없습니다.

## Render로 외부 배포하기

2026-09-19 현재, 이 저장소는 Render Blueprint `render.yaml`을 제공합니다. `1c-2g`(RAM 2GB) 웹 서비스와 2GB 영속 디스크를 선언하므로 **유료 리소스**입니다. Render 가격표 기준 웹 서비스는 월 약 US$25(계속 실행 시), 디스크는 GB당 월 US$0.25이며 사용량·세금·요금 변경에 따라 실제 청구액이 달라집니다. 서비스 생성 전에 Render 화면의 예상 요금을 확인하세요. 무료 웹 서비스는 영속 디스크를 연결할 수 없어 현재 SQLite 피드백·선호 기억을 보존할 수 없습니다.

1. GitHub `80gina/MM` 저장소의 `main` 브랜치에 최신 코드가 올라왔는지 확인합니다.
2. Render 대시보드에서 **New → Blueprint**를 선택하고 GitHub 계정을 연결한 뒤 `80gina/MM`을 선택합니다.
3. `render.yaml`의 웹 서비스 `mindily`, 플랜 `1c-2g`, 싱가포르 지역, 2GB 디스크 `/app/data`와 예상 비용을 확인하고 배포합니다. 계정 결제 수단이 필요할 수 있습니다.
4. 첫 시작에는 고정된 Hugging Face 모델을 내려받습니다. 모델 캐시는 `/app/data/hf-cache`에 저장됩니다. Render의 배포 상태가 Live가 될 때까지 기다립니다.
5. 발급된 `https://...onrender.com/api/health`에서 `status: ready`와 모델명을 확인합니다. 같은 주소의 `/`에서 모바일 UI를 열어 일기 분석, 추천, 만족도 제출·재시작 후 보존을 확인합니다.
6. 실제 URL, 날짜, Git 커밋, 헬스체크 화면, 모바일 시연 캡처를 `docs/제출증빙자료.md`와 `docs/시연보고서.md`에 기록합니다. 실제 사용자 5명의 동의 받은 테스트 결과만 기록합니다.

배포가 실패하면 Render 로그의 첫 오류를 확인합니다. 메모리 부족이면 더 큰 플랜이 필요하고, 모델 다운로드 실패면 Hugging Face 접근·저장 공간을 확인합니다. 영속 디스크가 붙은 서비스는 재배포 때 잠깐 중단될 수 있습니다. 일기 원문은 브라우저에 남고, 서버에는 동의한 피드백·선호만 저장하는 현재 방식도 공용 기기에서의 기록 노출 위험은 남으므로 사용자 안내를 유지합니다.

Vercel에는 현재 Python API 전체를 그대로 올리기 어렵습니다. Python Function의 압축 해제 후 크기 상한이 500MB이고 파일 저장이 영속적이지 않아, PyTorch 모델과 SQLite를 쓰는 이 구조에는 맞지 않습니다. UI만 Vercel에 분리하려면 API 주소·CORS·외부 DB를 새로 구성해야 합니다.

## 검증
requirements-dev.txt 설치 후 서버를 8010 포트에서 실행하고 python test_api.py를 실행합니다.
실제 가상 예문 검증 결과는 evidence/api-check.json입니다.

## 데이터 처리
분석 시 글이 이 앱의 서버로 전송되며 서버 코드는 원문을 저장하지 않습니다. 운영 호스팅의 로그 정책은 별도 확인이 필요합니다.
현재 브라우저 localStorage에 최대 30개 기록을 저장합니다. 같은 브라우저 사용자 간 분리와 기기 간 동기화는 미구현입니다.
일기 원문도 localStorage 기록에 포함됩니다. 공용 기기에서 사용하면 같은 브라우저의 다른 사람이 읽을 수 있으므로 마음 기록 화면의 삭제 버튼으로 기록을 지워야 합니다.
동의한 만족도 1~5점·선택 의견은 `data/feedback.sqlite3`에, 동의한 선호 활동 한 가지는 `data/memory.sqlite3`에 저장됩니다. 저장소의 토큰 해시로 선호를 조회·삭제하며 브라우저 토큰을 잃으면 즉시 조회·삭제할 수 없습니다. 30일 지난 선호는 다음 기억 요청 때 정리됩니다. 감정 정리하기 내용은 이 브라우저의 localStorage에만 저장되며 서버로 전송하지 않습니다. 운영 서비스에는 백업·보존기간·관리자 접근 통제가 추가로 필요합니다.
