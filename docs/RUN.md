# 실행과 배포 안내

Python 3.12 기준. 저장소 폴더에서 실행합니다.
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server:app --host 127.0.0.1 --port 8000 --no-access-log
```
http://127.0.0.1:8000 을 엽니다. 설치 후에는 START.cmd를 두 번 클릭합니다. 처음에는 모델 다운로드 시간이 필요합니다.
MINDILY_OFFLINE=1 환경변수로 이미 받은 모델을 오프라인 실행할 수 있습니다.
dist/index.html만 직접 열면 실제 분석 API를 사용할 수 없습니다.

일반 사용자는 배포 후 URL만 열면 되도록 구성합니다. 이번 버전의 외부 배포는 아직 검증하지 않았습니다.
Dockerfile은 배포 준비용이며 빌드·배포 성공 증빙이 아닙니다.
```sh
docker build -t mindily .
docker run --rm -p 8000:8000 -v mindily-models:/app/models mindily
```
모델 다운로드 공간·메모리·HTTPS·요청 제한·로그 정책을 확인한 뒤 배포합니다. GitHub Pages만으로 Python 모델을 실행할 수 없습니다.

## 검증
requirements-dev.txt 설치 후 서버를 8010 포트에서 실행하고 python test_api.py를 실행합니다.
실제 가상 예문 검증 결과는 evidence/api-check.json입니다.

## 데이터 처리
분석 시 글이 이 앱의 서버로 전송되며 서버 코드는 원문을 저장하지 않습니다. 운영 호스팅의 로그 정책은 별도 확인이 필요합니다.
현재 브라우저 localStorage에 최대 30개 기록을 저장합니다. 같은 브라우저 사용자 간 분리와 기기 간 동기화는 미구현입니다.
