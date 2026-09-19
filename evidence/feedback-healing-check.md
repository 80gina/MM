# 추천·만족도·선호 기억 검증 기록

- `python test_feedback.py`: 통과. 1~5점 만족도를 SQLite에 저장하고 새 연결에서 읽었으며, 동의 거부·범위 밖 점수·평가 누락이 저장되지 않음을 확인했다.
- `python test_healing.py`: 통과. 출처 URL 포함 카드 검색, 동의 거부, 선호 저장·조회, 추천 순서 변경, 삭제를 확인했다.
- `node --check dist/app.js`: 통과.
- `python -m py_compile server.py feedback_db.py memory_db.py healing_knowledge.py`: 통과.
- `http://127.0.0.1:8012/`: 로컬 모델 캐시를 지정해 서버가 시작되고 홈 화면이 브라우저에서 열린 것을 확인했다. 새 만족도·기억 화면의 수동 클릭 검증은 아직 남아 있다.
- Docker: 이 컴퓨터에서 `docker` 명령을 찾지 못해 이미지 빌드·영속 볼륨은 검증하지 못했다.

테스트는 가상 응답과 임시 SQLite 파일만 사용했다. 실제 사용자 5명 응답이나 외부 배포의 증빙이 아니다.
