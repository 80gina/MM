# 무료 임시 HTTPS 테스트: Cloudflare Quick Tunnel

2026-09-19에 로컬 Mindily 서버(8010 포트)를 Quick Tunnel로 연결하여 HTTPS 첫 화면(200), `/api/health`(`ready`), 가상의 일기 문장을 이용한 `/api/emotions/analyze`(모델 `GGARA02/kcelectra-korean-emotion`, 최상위 `기쁨`)를 확인했습니다. 주소는 세션마다 바뀌고 이 결과만으로 실제 사용자 5명 테스트·상시 배포가 완료된 것은 아닙니다.

## 처음 한 번만 준비

1. [Cloudflare 공식 Windows 다운로드 안내](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/)의 **64-bit Executable**을 받습니다.
2. 저장소 폴더에 `.local-tools` 폴더를 만들고 받은 파일을 `cloudflared.exe`라는 이름으로 넣습니다. 이 폴더는 GitHub에 올라가지 않습니다.
3. `./.local-tools/cloudflared.exe --version` 명령으로 실행을 확인합니다. 프로그램 설치 권한이나 Cloudflare 계정은 필요하지 않습니다.

## 매번 테스트할 때

1. 저장소 폴더에서 `START.cmd`를 실행하고 서버가 켜진 창을 그대로 둡니다. 처음 설치할 때는 [로컬 실행 순서](RUN.md)를 따릅니다. `http://127.0.0.1:8000/api/health`가 `ready`인지 확인합니다.
2. `START_QUICK_TUNNEL.cmd`를 두 번 클릭합니다. 서버가 8010 포트에서 실행 중이면 PowerShell에서 `./START_QUICK_TUNNEL.cmd 8010`을 실행합니다.
3. 새 창에 표시된 `https://...trycloudflare.com` 주소를 복사해 본인 휴대폰의 모바일 데이터로 접속합니다. 주소 끝에 `/api/health`를 붙여 모델 준비 상태도 확인합니다.
4. 동의한 테스트 참여자에게만 현재 세션 주소와 사용 시간을 알려줍니다. 가상의 일기로 먼저 분석·추천·만족도 등록을 확인하고, 이후 실제 사용자 5명의 결과를 [사용자 테스트 기록지](사용자테스트기록지.md)에 익명으로 기록합니다. **가상 테스트 응답을 실제 사용자 5건으로 세지 않습니다.**
5. 끝나면 터널 창에서 `Ctrl+C`로 종료하고 서버 창도 닫습니다. 컴퓨터가 잠자기 모드로 들어가거나 두 창이 닫히면 접속이 끊깁니다. 다시 시작하면 주소가 바뀔 수 있습니다.

Quick Tunnel은 [Cloudflare가 테스트·개발 전용이라고 설명](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)하며 가동 시간 보장이 없습니다. 주소를 아는 사람은 인증 없이 앱에 접근할 수 있습니다. 일기 원문은 사용자의 브라우저 저장소에 남고, 동의한 만족도·활동 선호만 이 컴퓨터의 `data/`에 저장되므로 공용 기기 사용을 피하고 테스트 후 필요하면 마음 기록을 삭제하도록 안내합니다. 컴퓨터의 방화벽 포트를 직접 열 필요는 없습니다.

## 증빙 작성

- 테스트 날짜·시간, 그때의 임시 URL, Git 커밋, `/api/health` 화면, 휴대폰 일기 분석 화면을 기록합니다. 임시 URL을 공개 GitHub 문서에 오래 남기지 말고 팀 제출 자료에만 기재합니다.
- 현재 세션의 URL과 자체 점검 결과는 로컬 `.local-tools/session.txt`에 기록할 수 있습니다. 이 파일은 Git에서 제외합니다.
- 임시 접근 성공은 **외부 HTTPS 시연 가능**을 입증하지만, 서버와 PC가 계속 켜져 있지 않아 상시 호스팅의 증거는 아닙니다.
