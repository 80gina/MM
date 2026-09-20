"""Check Docker COPY covers every local module imported by the app."""
import ast
import re
from pathlib import Path


root = Path(__file__).resolve().parent
dockerfile = (root / 'Dockerfile').read_text(encoding='utf-8')
copied = set()
for line in re.sub(r'\\\s*\n', ' ', dockerfile).splitlines():
    parts = line.split()
    if parts and parts[0] == 'COPY':
        copied.update(part for part in parts[1:-1] if part.endswith('.py'))

assert 'server.py' in copied, 'Dockerfile must copy the FastAPI entry point'
pending = ['server.py']
visited = set()
while pending:
    filename = pending.pop()
    if filename in visited:
        continue
    visited.add(filename)
    tree = ast.parse((root / filename).read_text(encoding='utf-8'))
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name.split('.')[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split('.')[0]]
        for name in names:
            local_file = f'{name}.py'
            if (root / local_file).exists():
                assert local_file in copied, f'Dockerfile omits local module: {local_file}'
                pending.append(local_file)

assert (root / 'dist' / 'index.html').exists() and 'dist ./dist' in dockerfile
print('Docker source copy covers local server imports and UI: OK')
