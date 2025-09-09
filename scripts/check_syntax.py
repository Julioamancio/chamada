import sys
from pathlib import Path

ok = True
for p in [Path('webapp/teacher.py')]:
    src = p.read_text(encoding='utf-8', errors='ignore')
    try:
        compile(src, str(p), 'exec')
        print('OK:', p)
    except Exception as e:
        print('ERROR:', p, e)
        ok = False
sys.exit(0 if ok else 1)

