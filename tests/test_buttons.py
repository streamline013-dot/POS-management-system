"""Dead-button audit (no button without a handler): collect every data-a action name rendered across all views
(plus static ones in the source) and check each has a handler in POS.ACT.
usage: python3 tests/test_buttons.py http://localhost:8039 index.html   (serve 01_APP first)"""
import sys, os, re, json
from playwright.sync_api import sync_playwright
base, src = sys.argv[1], sys.argv[2]
html = open(src, encoding='utf-8').read()
static = set(m for m in re.findall(r'data-a="([a-zA-Z_][\w]*)', html))
VIEWS = ['qlog','alerts','team','dev','dash','enc','board','hist','quotes','inv','rstock','prod','test','cat','mnt','cash','exp','close','fund','cap','pay','tax','ana','net','notes','co','set','bill','upd','help','ai']
seen = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROME') or None, args=['--no-sandbox'])
    pg = b.new_page(viewport={'width':1360,'height':900})
    pg.route('**/*', lambda r: r.abort() if not r.request.url.startswith(base) and not r.request.url.startswith('data:') else r.continue_())
    pg.goto(base + '/'); pg.wait_for_timeout(1500)
    pg.evaluate("()=>{const S=POS.S;S.set.payrollOn=true;S.set.taxOn=true;POS.save();POS.render()}")
    for v in VIEWS:
        pg.evaluate(f"()=>{{location.hash='#{v}'}}"); pg.wait_for_timeout(300)
        tabs = ['ov','feat','int','sec','bill','upd','ntc','log','data','sys'] if v=='dev' else [None]
        for t in tabs:
            if t: pg.evaluate(f"()=>POS.ACT.devtab('{t}')"); pg.wait_for_timeout(200)
            names = pg.evaluate("()=>[...document.querySelectorAll('[data-a]')].map(e=>e.dataset.a.split(':')[0])")
            for n in names: seen.setdefault(n, set()).add(v + (('/'+t) if t else ''))
    acts = set(pg.evaluate("()=>Object.keys(POS.ACT)"))
    b.close()
rt_missing = {n: sorted(w) for n, w in seen.items() if n not in acts}
st_missing = sorted(n for n in static if n not in acts)
print(json.dumps({'rendered_actions': len(seen), 'handlers': len(acts), 'rendered_missing': rt_missing, 'static_missing': st_missing}, indent=1))
sys.exit(1 if rt_missing or st_missing else 0)
