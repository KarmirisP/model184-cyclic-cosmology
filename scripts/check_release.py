#!/usr/bin/env python3
from pathlib import Path
import re,sys
R=Path(__file__).resolve().parents[1]
s=(R/'main.tex').read_text(); bib=(R/'references.bib').read_text()
keys=set()
for block in re.findall(r'\\cite\{([^}]+)\}',s): keys.update(k.strip() for k in block.split(','))
bibkeys=set(re.findall(r'@\w+\{([^,]+),',bib))
missing=sorted(keys-bibkeys)
print('citation_keys',len(keys),'bib_entries',len(bibkeys),'missing',missing)
print('brace_balance',s.count('{')-s.count('}'))
for f in (R/'scripts').glob('*.py'):
    compile(f.read_text(),str(f),'exec')
print('python_scripts=OK')
if missing or s.count('{')!=s.count('}'):
    sys.exit(1)
