"""실행 중인 로컬 서버에 가상 예문만 전송하여 확인."""
import json
from pathlib import Path
from datetime import datetime, timezone
import httpx

checks=[]
with httpx.Client(base_url='http://127.0.0.1:8010', timeout=60) as client:
    for name, payload, expected in [
        ('걱정 문장', {'text':'내일 발표가 걱정돼요.', 'self_reported_stress':4}, 200),
        ('빈 입력', {'text':' ', 'self_reported_stress':3}, 422),
        ('범위 밖 스트레스', {'text':'오늘의 마음', 'self_reported_stress':6}, 422),
        ('긴 글 분할', {'text':'오늘 여러 가지 일이 있어서 마음이 복잡했어요. '*25, 'self_reported_stress':2}, 200),
    ]:
        r=client.post('/api/emotions/analyze', json=payload)
        assert r.status_code==expected, (name,r.status_code)
        row={'case':name,'status':r.status_code}
        if expected==200:
            data=r.json()
            assert len(data['labels'])==6
            assert abs(sum(x['score'] for x in data['labels'])-1)<1e-5
            assert data['self_reported_stress']==payload['self_reported_stress']
            if name=='긴 글 분할': assert data['chunks']>1
            row.update(top=data['labels'][0],chunks=data['chunks'])
        checks.append(row)
    assert client.get('/').status_code==200
out=Path(__file__).parent/'evidence'/'api-check.json'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({'executed_at':datetime.now(timezone.utc).isoformat(),'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
print(out.read_text(encoding='utf-8'))
