#!/bin/sh
set -e
S=SCRATCH
cd $S
python3 final-audit/patch5.py $S
python3 build.py $S
python3 -I - <<'PY'
import re
t=open('fieldbook-redesign.html').read()
open('final-audit/extracted.js','w').write(re.search(r'<script>\n(.*)</script>',t,re.S).group(1))
head='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0;font-size:14px}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
open('final-audit/page.html','w').write(head+t+'</body></html>')
PY
node --check final-audit/extracted.js && echo SYNTAX_OK
