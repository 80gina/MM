"""Print aggregate satisfaction without revealing free-text responses."""
import sqlite3
from collections import Counter
from contextlib import closing

from feedback_db import database_path


path = database_path()
if not path.exists():
    print('아직 저장된 만족도 응답이 없습니다.')
else:
    with closing(sqlite3.connect(path)) as conn:
        rows = conn.execute(
            "SELECT satisfaction FROM feedback WHERE card_id='session-exit' AND satisfaction IS NOT NULL"
        ).fetchall()
    scores = [row[0] for row in rows]
    if scores:
        print(f'만족도 응답: {len(scores)}건')
        print(f'평균: {sum(scores) / len(scores):.2f}/5')
        print(f'점수별 건수: {dict(sorted(Counter(scores).items()))}')
        print('한 사람이 여러 번 제출할 수 있으므로 응답 수는 사용자 수가 아닙니다.')
    else:
        print('아직 저장된 만족도 응답이 없습니다.')
