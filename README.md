# Mindily MVP

AI 감정 일기와 맞춤형 힐링 코치를 시연하는 모바일 우선 웹 프로토타입입니다.

## 지금 가능한 흐름

1. 홈에서 오늘의 일기 작성
2. 감정 태그와 스트레스 정도 선택
3. 실제 KcELECTRA 모델의 6개 감정 분류 점수 확인
4. 무드 미터에서 세부 감정을 사용자가 직접 수정
5. 출처가 표시된 힐링 활동 추천과 1분 호흡, 템플릿 대화 시연
6. 브라우저 일기 기록과 사용 후 1~5점 만족도 저장
7. 동의한 선호 활동 한 종류 기억·삭제

## 중요한 구분

- 이번 소스의 감정 분석은 실제 GGARA02/kcelectra-korean-emotion API입니다. 외부 배포 갱신은 아직 하지 않았습니다.
- 모델 버전: 2eaf89d8d2cbfd902b93e5ec989db2ec103806fb. 출처·이용 조건은 https://huggingface.co/GGARA02/kcelectra-korean-emotion 을 확인합니다. `team_motion` 데이터로 소규모 추가 학습을 시험했으나 성능이 낮아 앱의 기본 모델은 공개 모델입니다.
- 채팅은 템플릿, 그래프·패턴은 예시, 미션은 짧은 시연입니다. 출처 검색형 활동 추천과 선호 기억은 구현했으나 생성형 Agent·LLM 기반 RAG·외부 배포·실제 5명 테스트는 미완료입니다.
- 만족도와 선호 기억은 서버 SQLite에, 일기 원문과 감정 기록은 브라우저 localStorage에 저장됩니다. 서버 저장에는 영속 디스크가 필요합니다.
- 공개 KcELECTRA 모델 연결 지점과 데이터 계약은 `docs/BEGINNER_ROADMAP.md`에 정리했습니다.
- 의료 진단이나 치료를 제공하지 않습니다.

## 로컬 실행

[초보자용 실행 안내](docs/RUN.md)를 따라 Python 서버를 실행하고 브라우저로 접속합니다. 설치 후 START.cmd로 실행할 수 있습니다. 일반 사용자는 이후 배포 URL만 열도록 구성합니다. 정적 파일만 열면 모델 API는 동작하지 않습니다.

## 제출 문서와 실제 확인 결과
- [기능명세서](docs/기능명세서.md)
- [체크리스트](docs/체크리스트.md)
- [미션 수행 체크리스트](docs/미션수행체크리스트.md)
- [팀 역할 및 기여 기록](docs/TEAM_ROLES.md)
- [프로그램 비평 및 향후 방향](docs/프로그램비평.md)
- [모델 학습 과정 및 결과](docs/모델학습보고서.md)
- [결과보고서](docs/결과보고서.md)
- [기술 통합 보고서](docs/INTEGRATION_REPORT.md)
- [시연보고서](docs/시연보고서.md)
- [시연계획서](docs/시연계획서.md)
- [제출증빙자료](docs/제출증빙자료.md)
- [피드백 기록](docs/피드백기록.md)
- [로컬 데이터 확인](docs/DATA_REFERENCE.md)
- [실제 API 검증 결과](evidence/api-check.json)
- [로컬 데이터 전수 통계](evidence/training-data-audit.json)
- [파일럿 추가 학습 결과](evidence/team-motion-training.json)

Dockerfile과 [Render 배포 설정](render.yaml)을 준비했습니다. 유료 웹 서비스·영속 디스크가 필요한 이유와 [초보자용 Render 배포 순서](docs/RUN.md#render로-외부-배포하기)를 확인하세요. 실제 배포·사용자 피드백 수집은 아직 완료되지 않았습니다.

비용 없이 과제 시연·5명 테스트를 진행할 때는 [Cloudflare Quick Tunnel 실행 안내](docs/QUICK_TUNNEL.md)를 사용합니다. 2026-09-19 임시 HTTPS 경로에서 첫 화면과 실제 모델 분석을 확인했습니다. PC와 서버를 켜 두어야 하며 상시 서비스 배포는 아닙니다.

만족도 응답은 `python feedback_summary.py`로 개인 의견을 출력하지 않고 집계할 수 있습니다. 응답 5건은 서로 다른 사용자 5명을 증명하지 않으므로 별도 동의·테스트 기록이 필요합니다.

## 폴더

- `dist/`: 배포 가능한 정적 앱
- `docs/BEGINNER_ROADMAP.md`: 초보자용 팀 개발 순서, 역할, 모델 연동 계약

