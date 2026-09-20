#!/usr/bin/env bash
# Hugging Face Space 배포 스크립트
#
# 사전 준비 (최초 1회)
#   1. https://huggingface.co/new-space 에서 Space 생성
#      - Space name: mindily
#      - SDK: Docker  /  Hardware: CPU basic (무료)  /  Visibility: Public
#   2. Settings → Variables and secrets 에서 코디세이 API 값 등록
#      CODYSSEY_API_KEY(Secret) · CODYSSEY_API_BASE · CODYSSEY_MODEL
#   3. huggingface-cli login  (또는 HF_TOKEN 환경 변수)
#
# 사용법
#   ./deploy_space.sh yellowmug
set -euo pipefail

USER="${1:?사용법: ./deploy_space.sh yellowmug}"
SPACE="mindily"
TMP="$(mktemp -d)"

echo "▶ Space 저장소를 임시 폴더로 복제합니다."
git clone "https://huggingface.co/spaces/${USER}/${SPACE}" "$TMP/space"

echo "▶ 배포에 필요한 파일만 복사합니다."
cp Dockerfile requirements.txt "$TMP/space/"
cp server.py coach_agent.py rag.py llm.py diary_draft.py \
   feedback_db.py healing_knowledge.py memory_db.py "$TMP/space/"
rm -rf "$TMP/space/dist" && cp -r dist "$TMP/space/dist"

# Space의 README.md는 YAML 프런트매터가 필요하므로 전용 파일을 사용한다.
cp SPACE_README.md "$TMP/space/README.md"

echo "▶ 커밋하고 푸시합니다. (빌드는 Space에서 자동 시작됩니다)"
cd "$TMP/space"
git add -A
git commit -m "Deploy Mindily $(date +%Y-%m-%d)" || echo "변경 사항 없음"
git push

echo
echo "✅ 완료: https://huggingface.co/spaces/${USER}/${SPACE}"
echo "   빌드 상태는 Space 페이지의 Logs 탭에서 확인하세요 (최초 빌드 약 10~15분)."
echo "   빌드 후 확인:  curl https://${USER}-${SPACE}.hf.space/api/health"
