"""원문을 출력하지 않고 로컬 데이터 구조만 확인합니다."""
import json
import sys
from pathlib import Path
from collections import Counter

root = Path(sys.argv[1])
summary = {'folders': [], 'note': '압축 해제된 JSON 중 그룹별 첫 파일의 구조만 확인. 전체 데이터 통계 아님.'}
for group in sorted(root.iterdir()):
    if not group.is_dir():
        continue
    files = sorted(group.rglob('*.json'))
    row = {'group': group.name, 'extracted_json_files': len(files), 'zip_files': len(list(group.rglob('*.zip')))}
    if files:
        data = json.loads(files[0].read_text(encoding='utf-8-sig'))
        fields = {}; emotions = Counter()
        def walk(value, path='', depth=0):
            if depth > 8: return
            if isinstance(value, dict):
                for key, item in value.items():
                    here = path + '.' + key
                    fields[here] = type(item).__name__
                    if isinstance(item, str) and any(x in key.lower() for x in ['emotion', '감정']):
                        emotions[item] += 1
                    walk(item, here, depth + 1)
            elif isinstance(value, list):
                for item in value[:3]: walk(item, path+'[]', depth+1)
        walk(data)
        row.update(fields=fields, sample_emotion_values=dict(emotions))
    summary['folders'].append(row)
out = Path(__file__).parent / 'evidence' / 'data-schema.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(out.read_text(encoding='utf-8'))
