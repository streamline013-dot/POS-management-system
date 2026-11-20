"""Open every page in LOCAL mode (no Firebase), light and dark, and report JavaScript errors.
usage: python3 test_views.py http://localhost:8039 ./shots   (serve 01_APP first: python3 -m http.server 8039)"""
import sys, os, json
from playwright.sync_api import sync_playwright
base, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
VIEWS = ['dash','enc','qlog','alerts','board','hist','quotes','inv','rstock','prod','test','cat','mnt','cash','exp','close','fund','cap','pay','tax','ana','net','notes','co','set','bill','team','dev','upd','help','ai']
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROME') or None, args=['--no-sandbox'])
    for scheme in ['light', 'dark']:
        ctx = b.new_context(viewport={'width': 1360, 'height': 900}, color_scheme=scheme)
        pg = ctx.new_page()
        pg.on('console', lambda m: errs.append((scheme, 'console', m.text)) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errs.append((scheme, 'pageerror', str(e))))
        pg.route('**/*', lambda r: r.abort() if not r.request.url.startswith(base) and not r.request.url.startswith('data:') else r.continue_())
        pg.goto(base + '/'); pg.wait_for_timeout(1500)
        pg.evaluate("()=>{const S=POS.S;S.set.payrollOn=true;S.set.taxOn=true;POS.save();POS.render()}")
        for v in VIEWS:
            pg.evaluate(f"()=>{{location.hash='#{v}'}}"); pg.wait_for_timeout(300)
            pg.screenshot(path=f"{out}/{scheme}_{v}.png")
        pg.evaluate("()=>{location.hash='#dev'}"); pg.wait_for_timeout(300)
        for t in ['ov','feat','int','sec','bill','upd','ntc','log','data','sys']:
            pg.evaluate(f"()=>POS.ACT.devtab('{t}')"); pg.wait_for_timeout(300)
            pg.screenshot(path=f"{out}/{scheme}_dev_{t}.png")
        if scheme == 'light':  # page end: small gap on desktop; on phones the last card stays above the tab bar
            for w, h in [(1360, 900), (390, 844)]:
                pg.set_viewport_size({'width': w, 'height': h})
                for v in ['fund', 'cat', 'dash', 'set']:
                    pg.evaluate(f"()=>{{location.hash='#{v}'}}"); pg.wait_for_timeout(250)
                    m = pg.evaluate("()=>{window.scrollTo(0,1e6);const last=[...document.querySelector('#v').children].filter(e=>e.offsetParent).pop(),tb=document.querySelector('#tabbar'),tbh=tb&&getComputedStyle(tb).display!=='none'?tb.getBoundingClientRect().height:0;return{gap:document.documentElement.scrollHeight-(last.getBoundingClientRect().bottom+scrollY),tbh}}")
                    if not (m['tbh'] <= m['gap'] <= m['tbh'] + 48):
                        errs.append((scheme, 'spacing', f"{v} @{w}px: gap {round(m['gap'])}px, tab bar {round(m['tbh'])}px"))
            pg.set_viewport_size({'width': 1360, 'height': 900})
        ctx.close()
    b.close()
print(json.dumps(errs, indent=1)); print('PASS' if not errs else 'FAIL', (len(VIEWS) + 10) * 2, 'page renders checked')
