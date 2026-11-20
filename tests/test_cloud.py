"""End-to-end test of cloud mode (v39.1) against a MOCK Firebase (auth + realtime database that enforces the generated rules).
Covers: shop login vs Developer portal + Developer PIN (rules-enforced session), roles, invites, access requests,
front-page Quick Log with desk code, alerts, billing + soft lock, update notes, appearance, history, presence and remote sign-out.
usage: python3 tests/test_cloud.py http://localhost:8039 ./shots/cloud   (serve 01_APP first)"""
import sys, os, json, time, datetime
from playwright.sync_api import sync_playwright

BASE, SHOTS = sys.argv[1], sys.argv[2]
os.makedirs(SHOTS, exist_ok=True)
MOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mockfb')
CFG = """window.POS_CONFIG={firebase:{apiKey:'AIzaTESTKEY123456',authDomain:'printshop-test.firebaseapp.com',databaseURL:'https://printshop-test-default-rtdb.asia-southeast1.firebasedatabase.app',projectId:'printshop-test',appId:'1:123:web:abc'},developers:['micah.dev@gmail.com'],shopId:'main',firebaseSdkVersion:'13.4.0',googleDriveClientId:''};"""
ACCTS = {'dev': {'uid': 'u_dev', 'email': 'micah.dev@gmail.com', 'displayName': 'Micah Joy'},
         'admin': {'uid': 'u_adm', 'email': 'ana.admin@gmail.com', 'displayName': 'Ana Reyes'},
         'staff': {'uid': 'u_stf', 'email': 'ben.staff@gmail.com', 'displayName': 'Ben Cruz'},
         'stranger': {'uid': 'u_x', 'email': 'x.someone@gmail.com', 'displayName': 'Some One'}}
PIN = 'devpin2026'
DBM = "https://www.gstatic.com/firebasejs/13.4.0/firebase-database.js"
errs, results = [], []
def ok(name, cond, extra=''):
    results.append((name, bool(cond), extra)); print(('PASS ' if cond else 'FAIL ') + name + (' — ' + str(extra)[:300] if extra and not cond else ''))
def denied(op):  # JS snippet: returns true when the mock database refuses the operation
    return f"async()=>{{const m=await import('{DBM}');try{{{op};return false}}catch(e){{return /PERMISSION/.test(e.code)}}}}"
def allowed(op):
    return f"async()=>{{const m=await import('{DBM}');try{{{op};return true}}catch(e){{return false}}}}"
D = lambda n: (datetime.date.today() + datetime.timedelta(days=n)).isoformat()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get('CHROME') or None, args=['--no-sandbox'])
    ctx = b.new_context(viewport={'width': 1360, 'height': 900}, accept_downloads=True)
    ctx.add_init_script(f"localStorage.setItem('__mock_accounts', {json.dumps(json.dumps(ACCTS))});")
    def route(r):
        u = r.request.url
        if u.startswith('https://www.gstatic.com/firebasejs/'):
            return r.fulfill(path=os.path.join(MOCK, u.rsplit('/', 1)[-1]), content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'})
        if u.startswith(BASE + '/app-config.js'):
            return r.fulfill(body=CFG, content_type='application/javascript')
        if u.startswith(BASE) or u.startswith('data:') or u.startswith('blob:'):
            return r.continue_()
        return r.abort()
    ctx.route('**/*', route)
    DLG = {'accept': True, 'prompt': None, 'seen': []}
    def on_dialog(d):
        DLG['seen'].append(d.message[:160])
        if d.type == 'prompt' and DLG['prompt'] is not None: d.accept(DLG['prompt'])
        elif DLG['accept']: d.accept()
        else: d.dismiss()
    def mkpage():
        pg = ctx.new_page()
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)))
        pg.on('dialog', on_dialog)
        return pg
    pg = mkpage()
    ev = lambda js, *a: pg.evaluate(js, *a)
    def wait(cond, t=6000, page=None):
        try: (page or pg).wait_for_function(cond, timeout=t); return True
        except Exception: return False
    def db(): return ev("()=>JSON.parse(localStorage.getItem('__mock_db')||'{}')")
    def shop(): return db().get('shops', {}).get('main', {})
    def click_signin(who, page=None):
        page = page or pg
        page.evaluate(f"localStorage.setItem('__mock_next','{who}')"); page.click('#lock .gbtn')
    def signin(who, page=None):  # shop login (admin / staff / stranger)
        page = page or pg
        page.evaluate("POS.ACT.gportal('shop')"); wait("()=>document.querySelector('#lock .gbtn')", page=page)
        click_signin(who, page)
    def devsignin(new=False, pin=PIN):
        ev("POS.ACT.gportal('dev')"); wait("()=>document.querySelector('#lock.devp .gbtn')")
        click_signin('dev'); wait("()=>document.querySelector('#g-dpin')", 8000)
        pg.fill('#g-dpin', pin)
        if new: pg.fill('#g-dpin2', pin)
        pg.press('#g-dpin', 'Enter')
        return wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='developer'", 8000)
    def signout(page=None):
        page = page or pg
        page.evaluate("POS.ACT.gout()"); wait("()=>document.querySelector('#lock .gbtn')", page=page)

    pg.goto(BASE + '/')
    ok('gate shows sign-in', wait("()=>document.querySelector('#lock .gbtn')"))
    rules = ev("POS.cloud.rules()"); json.loads(rules)
    ok('generated rules are valid JSON', True)
    open(os.path.join(SHOTS, 'rules.json'), 'w').write(rules)
    ev(f"localStorage.setItem('__mock_rules', {json.dumps(rules)})")
    pg.reload(); wait("()=>document.querySelector('#lock .gbtn')")
    ok('front-page Quick Log hidden until an admin turns it on', not ev("!!document.querySelector('#lock .g-ql')"))
    ok('footer has a Developer portal link', ev("!!document.querySelector('#lock .g-pl[data-a=\"gportal:dev\"]')"))
    pg.screenshot(path=f'{SHOTS}/01_signin.png')

    # ---- developer: separate portal + Developer PIN ----
    signin('dev')
    ok('developer on the shop login is sent to the Developer portal', wait("()=>document.querySelector('#lock [data-a=\"gportal:dev\"].p')", 8000))
    pg.screenshot(path=f'{SHOTS}/02_devonly.png')
    pg.click('#lock [data-a="gportal:dev"].p')
    ok('first visit asks to create a Developer PIN', wait("()=>document.querySelector('#g-dpin2')&&document.querySelector('#lock.devp')", 8000))
    pg.fill('#g-dpin', 'abc12345'); pg.fill('#g-dpin2', 'abc99999'); pg.press('#g-dpin', 'Enter'); pg.wait_for_timeout(300)
    ok('PIN mismatch is caught', ev("!!document.querySelector('#lock .g-err')"))
    pg.screenshot(path=f'{SHOTS}/03_devpin_create.png')
    pg.fill('#g-dpin', PIN); pg.fill('#g-dpin2', PIN); pg.press('#g-dpin', 'Enter')
    ok('developer gets in after the PIN', wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='developer'", 8000), ev("POS.cloud.state()"))
    s = shop()
    ok('developer session stored with expiry', (s.get('devsess', {}).get('u_dev') or {}).get('exp', 0) > time.time() * 1000)
    ok('developer lands on the Developer Console', ev("location.hash")=='#dev')
    ok('PIN hash cannot be read, salt can (rules)', ev(denied("await m.get(m.ref({}, 'shops/main/devkey/micah,dev@gmail,com/h'))")) and ev(allowed("await m.get(m.ref({}, 'shops/main/devkey/micah,dev@gmail,com/s'))")))
    ok('developer member record written', (s.get('members', {}).get('u_dev') or {}).get('role') == 'developer')
    ok('realtime sync connected', wait("()=>POS.cloud.state().sync.on", 8000))
    ok('shop data uploaded to cloud', len((shop().get('d') or {}).get('c', {})) > 0)
    ok('sign-in logged', any(v.get('ok') and v.get('portal') == 'dev' for v in shop().get('logins', {}).values()))
    # features + notice
    ev("POS.ACT.devtab('feat')"); pg.wait_for_timeout(300)
    pg.click('input[data-feat="pay"]', force=True); pg.wait_for_timeout(500)
    ok('feature saved to config', (shop().get('config', {}).get('features', {}) or {}).get('pay') is True)
    ev("POS.ACT.devtab('ntc')"); pg.wait_for_timeout(200); pg.fill('#nt-m', 'Inventory count on Friday 6PM'); ev("POS.ACT.dvntc('on')"); pg.wait_for_timeout(400)
    ok('announcement banner shows', ev("!!document.querySelector('#notice .notice')"))
    for t in ['ov', 'feat', 'int', 'sec', 'bill', 'upd', 'ntc', 'log', 'data', 'sys']:
        ev(f"POS.ACT.devtab('{t}')"); pg.wait_for_timeout(450); pg.screenshot(path=f'{SHOTS}/04_dev_{t}.png', full_page=True)
    ev("POS.ACT.devtab('int')"); pg.wait_for_timeout(200); ev("POS.ACT.dvrp()"); pg.wait_for_timeout(400)
    ok('rules check says the rules match', ev("document.querySelector('.rp-line .b.ok')!==null"))
    # update note
    ev("POS.ACT.devtab('upd')"); pg.wait_for_timeout(200); pg.fill('#un-title', 'New: front-page Quick Log'); pg.fill('#un-body', '- Log jobs on the login page\n- Ask the admin for the desk code'); ev("POS.ACT.unsave()"); pg.wait_for_timeout(400)
    ok('update note published', len(shop().get('upd', {})) == 1)
    # team
    ev("location.hash='#team'"); pg.wait_for_timeout(300); DLG['accept'] = False
    pg.fill('#inv-e', 'ANA.Admin@gmail.com'); pg.select_option('#inv-r', 'admin'); pg.click('form[data-invform] button.p'); pg.wait_for_timeout(500)
    pg.fill('#inv-e', 'ben.staff@gmail.com'); pg.select_option('#inv-r', 'staff'); pg.click('form[data-invform] button.p'); pg.wait_for_timeout(500)
    DLG['accept'] = True
    inv = shop().get('invites', {})
    ok('invites written', 'ana,admin@gmail,com' in inv and 'ben,staff@gmail,com' in inv, list(inv))
    # an order and a quick log entry
    ev("""()=>{const P=POS;P.E=P.newE();const E=P.E;E.customer='Liza';const it=E.items[0];it.project='Tarpaulin 3x5';it.qty='2';it.actual='350';E.ptype='dp50';P.ACT.stx()}""")
    ev("location.hash='#qlog'"); pg.wait_for_timeout(300); pg.fill('#ql-title', '30 pcs ref magnets — Mia'); pg.click('form[data-qlform] button[type=submit]'); pg.wait_for_timeout(700)
    ok('quick log saved', ev("POS.S.qlog.length")==1)
    # front-page Quick Log settings
    pg.click('input[data-fqlon]', force=True); pg.wait_for_timeout(500)
    pg.fill('#fql-code', '4821'); ev("POS.ACT.fqlcode('save')"); pg.wait_for_timeout(500)
    s = shop()
    ok('front-page Quick Log turned on with a desk code', (s.get('pub', {}).get('ql') or {}).get('on') is True and (s.get('pub', {}).get('ql') or {}).get('code') is True and (s.get('qlsec') or {}).get('code') == '4821', s.get('pub'))
    pg.screenshot(path=f'{SHOTS}/05_qlog_settings.png', full_page=True)
    ok('cloud got the order + quick log', wait("()=>{const d=JSON.parse(localStorage.getItem('__mock_db'));const c=d.shops.main.d.c;return c.qlog&&Object.keys(c.qlog).length===1&&c.tx&&Object.keys(c.tx).length>=1}", 5000))
    pg.wait_for_timeout(21000)  # let the grouped "data.change" history entry flush
    acts = [v.get('act') for v in shop().get('audit', {}).values()]
    ok('history has order + data-change entries', 'order.save' in acts and 'data.change' in acts, acts)
    # history tab + CSV
    ev("location.hash='#dev'"); pg.wait_for_timeout(200); ev("POS.ACT.devtab('log')"); pg.wait_for_timeout(800); ev("POS.ACT.dvht('in')"); pg.wait_for_timeout(300)
    ok('sign-in history lists the developer', ev("[...document.querySelectorAll('.lgsc tr')].some(r=>r.textContent.includes('micah.dev@gmail.com'))"))
    with pg.expect_download() as dl: ev("POS.ACT.dvcsv()")
    ok('history CSV downloads', dl.value.suggested_filename.startswith('sign-ins-'))
    pg.screenshot(path=f'{SHOTS}/06_history.png', full_page=True)
    # session lock → rules refuse data until the PIN is entered again
    ev("POS.ACT.devlock()")
    ok('locking the developer session asks for the PIN', wait("()=>document.querySelector('#g-dpin')&&!document.querySelector('#g-dpin2')", 6000))
    ok('without a session the developer cannot read shop data (rules)', ev(denied("await m.get(m.ref({}, 'shops/main/d'))")))
    pg.fill('#g-dpin', 'wrongpin1'); pg.press('#g-dpin', 'Enter'); pg.wait_for_timeout(500)
    ok('wrong Developer PIN rejected by the rules', ev("!!document.querySelector('#lock .g-err')") and any((not v.get('ok')) and v.get('why') == 'pin' for v in shop().get('logins', {}).values()))
    pg.screenshot(path=f'{SHOTS}/07_devpin_wrong.png')
    pg.fill('#g-dpin', PIN); pg.press('#g-dpin', 'Enter')
    ok('right PIN opens a new session', wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='developer'", 8000))
    # expired session on reload
    ev("()=>{const k=Object.keys(localStorage).find(x=>x.startsWith('pos_devsess:'));localStorage.setItem(k,JSON.stringify({exp:Date.now()-1000}));const d=JSON.parse(localStorage.getItem('__mock_db'));d.shops.main.devsess.u_dev.exp=Date.now()-1000;localStorage.setItem('__mock_db',JSON.stringify(d))}")
    pg.reload()
    ok('expired developer session asks for the PIN after reload', wait("()=>document.querySelector('#g-dpin')", 8000))
    pg.fill('#g-dpin', PIN); pg.press('#g-dpin', 'Enter'); wait("()=>!document.body.classList.contains('gated')", 8000)
    signout()
    ok('sign-out removes the developer session', not (shop().get('devsess') or {}).get('u_dev'))

    # ---- front page: Quick Log without signing in ----
    ev("POS.ACT.gportal('shop')"); pg.reload()
    ok('front-page Quick Log shows on the login page', wait("()=>document.querySelector('#lock .g-ql form[data-fqlform]')", 8000))
    pg.screenshot(path=f'{SHOTS}/08_front_ql.png')
    pg.click('#lock .fql-go'); pg.wait_for_timeout(200)
    ok('empty title is refused', ev("!!document.querySelector('#lock .fql-err')"))
    pg.fill('#lock [name="t"]', '100 pcs calling cards — Rico'); pg.fill('#lock [name="c"]', 'Rico'); pg.fill('#lock [name="q"]', '100')
    pg.click('#lock .fql-go'); pg.wait_for_timeout(300)
    ok('desk code required', ev("(document.querySelector('#lock .fql-err')||{}).textContent||''").lower().find('desk code') >= 0)
    pg.fill('#lock [name="k"]', '0000'); pg.click('#lock .fql-go'); pg.wait_for_timeout(700)
    ok('wrong desk code refused by the rules', ev("(document.querySelector('#lock .fql-err')||{}).textContent||''") != '' and not shop().get('qlin'))
    pg.fill('#lock [name="t"]', '100 pcs calling cards — Rico'); pg.fill('#lock [name="by"]', 'Front desk'); pg.fill('#lock [name="k"]', '4821'); ev("POS.ACT.fqlp('high')"); pg.wait_for_timeout(150)
    pg.fill('#lock [name="t"]', '100 pcs calling cards — Rico'); pg.fill('#lock [name="k"]', '4821'); pg.click('#lock .fql-go')
    ok('right desk code sends the job', wait("()=>document.querySelector('#lock .fql-done')", 6000) and len(shop().get('qlin', {})) == 1)
    item = list(shop().get('qlin', {}).values())[0] if shop().get('qlin') else {}
    ok('inbox item has the details', item.get('t') == '100 pcs calling cards — Rico' and item.get('p') == 'high' and item.get('q') == 100, item)
    pg.screenshot(path=f'{SHOTS}/09_front_ql_done.png')
    ok('signed-out visitor cannot read the inbox (rules)', ev(denied("await m.get(m.ref({}, 'shops/main/qlin'))")))
    ok('signed-out visitor cannot read shop data (rules)', ev(denied("await m.get(m.ref({}, 'shops/main/d'))")))
    ok('extra fields are refused (rules)', ev(denied("await m.set(m.ref({}, 'shops/main/qlin/zz1'),{t:'Spam test',at:1,k:'4821',evil:'x'})")))
    pg.set_viewport_size({'width': 390, 'height': 844}); pg.wait_for_timeout(300)
    ok('phone: Quick Log button on the login card', ev("getComputedStyle(document.querySelector('#lock .g-qlbtn')).display!=='none'"))
    ev("POS.ACT.fqlview('1')"); pg.wait_for_timeout(300); ev("POS.ACT.fqlnew()"); pg.wait_for_timeout(200)
    ok('phone: Quick Log opens full screen', ev("getComputedStyle(document.querySelector('#lock .g-ql')).display!=='none'&&getComputedStyle(document.querySelector('#lock .g-card')).display==='none'"))
    pg.screenshot(path=f'{SHOTS}/10_front_ql_phone.png', full_page=True)
    ev("POS.ACT.fqlview('0')"); pg.set_viewport_size({'width': 1360, 'height': 900})

    # ---- stranger: no access + access request ----
    signin('stranger')
    ok('uninvited account sees "no access"', wait("()=>document.querySelector('#lock .g-who')&&document.body.classList.contains('gated')", 8000))
    pg.wait_for_timeout(400)
    ok('access request recorded', 'x,someone@gmail,com' in shop().get('reqs', {}))
    ok('stranger cannot self-invite (rules)', ev(denied("await m.set(m.ref({}, 'shops/main/members/u_x'),{role:'staff',email:'x.someone@gmail.com'})")))
    ev("POS.ACT.gout()"); pg.wait_for_timeout(300)

    # ---- staff ----
    signin('staff')
    ok('invited staff gets in', wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='staff'", 8000), ev("POS.cloud.state()"))
    wait("()=>POS.cloud.state().sync.on", 6000)
    ok('front-page job moved into the Quick Log once', wait("()=>POS.S.qlog.filter(x=>x.src==='front').length===1", 8000) and not shop().get('qlin'), ev("POS.S.qlog.map(x=>x.title)"))
    pg.wait_for_timeout(600)
    ok('staff sees synced data', ev("POS.S.qlog.length")==2 and ev("POS.groups().length")>=1)
    navs = ev("[...document.querySelectorAll('#nav a')].map(a=>a.getAttribute('href').slice(1))")
    ok('staff nav hides money/setup/team/dev/billing', not any(v in navs for v in ['cash', 'set', 'team', 'dev', 'fund', 'ana', 'bill']) and 'alerts' in navs, navs)
    ok('staff cannot change config (rules)', ev(denied("await m.set(m.ref({}, 'shops/main/config/features/pay'),false)")))
    ok('staff cannot promote self (rules)', ev(denied("await m.update(m.ref({}, 'shops/main/members/u_stf'),{role:'admin'})")))
    ok('staff cannot clear a sign-out request (rules)', ev(denied("await m.update(m.ref({}, 'shops/main/members/u_stf'),{kick:1})")))
    ok('staff cannot read billing (rules)', ev(denied("await m.get(m.ref({}, 'shops/main/bill'))")))
    ok('staff cannot read admin alerts (rules)', ev(denied("await m.get(m.ref({}, 'shops/main/alerts/admin'))")))
    ok('staff cannot send to everyone (rules)', ev(denied("await m.set(m.ref({}, 'shops/main/alerts/all/zz'),{t:'x',lv:'info',by:'u_stf',at:'x'})")))
    ev("POS.ACT.alnew()"); pg.wait_for_timeout(300)
    ok('staff can only send to admins or the developer', ev("[...document.querySelectorAll('#al-to option')].map(o=>o.value).join()") == 'admin,dev')
    pg.fill('#al-t', 'Printer #2 is out of cyan ink'); pg.fill('#al-b', 'Need a refill before the 3PM batch.'); pg.select_option('#al-lv', 'warn'); ev("POS.ACT.alsend()"); pg.wait_for_timeout(500)
    ok('staff alert stored for admins', len((shop().get('alerts') or {}).get('admin', {})) == 1)
    pg.screenshot(path=f'{SHOTS}/11_staff_dash.png')
    signout()

    # ---- admin (page 1) + staff (page 2) at the same time ----
    signin('admin')
    ok('invited admin gets in', wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='admin'", 8000))
    pg.wait_for_timeout(1500)
    ok('admin bell shows unread alerts', ev("POS.alerts.count()") >= 2, ev("POS.alerts.list().map(x=>x.t)"))
    ev("POS.ACT.alerts()"); pg.wait_for_timeout(300); pg.screenshot(path=f'{SHOTS}/12_admin_bell.png')
    ok('bell lists the staff message and the update note', ev("(()=>{const t=document.querySelector('.pop.alp').textContent;return t.includes('cyan ink')&&t.includes('front-page Quick Log')})()"))
    ev("POS.UI.closePop()")
    ev("location.hash='#team'"); pg.wait_for_timeout(500)
    ok('admin sees the access request', ev("!!document.querySelector('.rqcard')"))
    pg.screenshot(path=f'{SHOTS}/13_team_admin.png', full_page=True)
    ev("POS.ACT.rqok('x,someone@gmail,com','staff')"); pg.wait_for_timeout(500)
    ok('one-tap invite from the request', 'x,someone@gmail,com' in shop().get('invites', {}) and 'x,someone@gmail,com' not in shop().get('reqs', {}))
    ok('admin cannot create admin invite (rules)', ev(denied("await m.set(m.ref({}, 'shops/main/invites/z,z@gmail,com'),{role:'admin',email:'z.z@gmail.com'})")))
    # appearance
    ev("location.hash='#co'"); pg.wait_for_timeout(300); ev("POS.ACT.uiset('pal','ocean')"); ev("POS.ACT.uiset('font','jakarta')"); ev("POS.ACT.uiset('side','light')"); pg.wait_for_timeout(300)
    ok('appearance saved for the shop', ev("POS.S.set.ui.pal==='ocean'&&POS.S.set.ui.font==='jakarta'"))
    ok('palette applied', ev("getComputedStyle(document.documentElement).getPropertyValue('--ac').trim().toUpperCase()")=='#1F5F8B')
    ok('font applied', 'PJSV' in ev("getComputedStyle(document.body).fontFamily"))
    pg.evaluate("document.getElementById('uicard').scrollIntoView()"); pg.wait_for_timeout(200); pg.screenshot(path=f'{SHOTS}/14_appearance.png')
    pg.wait_for_timeout(2800)
    ok('look published for the login page', ((shop().get('pub') or {}).get('theme') or {}).get('pal') == 'ocean')
    # page 2: staff signs in on another device
    pg2 = mkpage(); pg2.goto(BASE + '/'); wait("()=>window.POS&&POS.cloud", 8000, pg2); pg2.wait_for_timeout(1200)
    pg2.evaluate("POS.ACT.gout()"); wait("()=>document.querySelector('#lock .gbtn')", 6000, pg2)
    signin('staff', pg2)
    ok('staff signs in on a second device', wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='staff'", 8000, pg2))
    pg2.wait_for_timeout(800)
    ev("POS.ACT.alnew()"); pg.wait_for_timeout(300); pg.select_option('#al-to', 'staff'); pg.select_option('#al-lv', 'urgent'); pg.fill('#al-t', 'Close the shop at 5PM today'); pg.fill('#al-b', 'Power interruption from 5PM.'); ev("POS.ACT.alsend()")
    ok('urgent alert pops up on the staff device', wait("()=>!!document.querySelector('.mdl .al-d')", 6000, pg2))
    pg2.screenshot(path=f'{SHOTS}/15_staff_urgent.png')
    pg2.evaluate("POS.closeModal()")
    ok('reading marks it read for that person', wait("()=>{const d=JSON.parse(localStorage.getItem('__mock_db'));return Object.keys((d.shops.main.ar||{}).u_stf||{}).length>0}", 4000, pg2))
    pg2.wait_for_timeout(400); ev("POS.render()"); pg.wait_for_timeout(300)
    ok('admin sees staff online', ev("POS.cloud.team.online().some(o=>o.id==='u_stf')"))
    ev("POS.ACT.dvkickgo('u_stf','0')")
    ok('remote sign-out reaches the staff device', wait("()=>document.body.classList.contains('gated')&&!!document.querySelector('#lock .gbtn')", 8000, pg2))
    pg2.close()
    ev("location.hash='#team'"); pg.wait_for_timeout(400)
    pg.click('input[data-pol="cash"]', force=True); pg.wait_for_timeout(500)
    pol = shop().get('policy', {}).get('staffDeny', []); pol = list(pol.values()) if isinstance(pol, dict) else pol
    ok('admin opened Cash Flow to staff', 'cash' not in pol and 'ana' in pol, pol)
    ev("POS.ACT.mrm('u_stf')"); pg.wait_for_timeout(500)
    ok('admin removed staff', 'u_stf' not in shop()['members'])
    ev("location.hash='#upd'"); pg.wait_for_timeout(300)
    ok("What's new lists the developer note", ev("document.querySelector('#v').textContent.includes('front-page Quick Log')"))
    pg.screenshot(path=f'{SHOTS}/16_whatsnew.png', full_page=True)
    signout()
    ok('login page keeps the shop look', ev("getComputedStyle(document.documentElement).getPropertyValue('--ac').trim().toUpperCase()")=='#1F5F8B')

    # ---- billing: developer sets an overdue plan with soft lock ----
    ok('developer signs in again with the PIN', devsignin())
    ev("location.hash='#dev'"); pg.wait_for_timeout(200); ev("POS.ACT.devtab('bill')"); pg.wait_for_timeout(300)
    pg.fill('#bp-name', 'POS Monthly'); pg.fill('#bp-amt', '499'); pg.select_option('#bp-cyc', 'monthly'); pg.fill('#bp-due', D(-10)); pg.fill('#bp-grace', '3'); pg.check('#bp-lock', force=True)
    ev("POS.ACT.blsave()"); pg.wait_for_timeout(500)
    s = shop()
    ok('plan saved + staff copy (billgate)', (s.get('bill', {}).get('plan') or {}).get('amt') == 499 and (s.get('billgate') or {}).get('lock') is True, s.get('billgate'))
    ev("POS.ACT.bltab('meth')"); pg.wait_for_timeout(200); ev("POS.ACT.blmeth()"); pg.wait_for_timeout(300)
    pg.fill('#bm-label', 'GCash'); pg.fill('#bm-acn', 'Micah J.'); pg.fill('#bm-num', '0917 123 4567'); ev("POS.ACT.blmsave('')"); pg.wait_for_timeout(500)
    ok('payment method saved', len(shop().get('bill', {}).get('meth', {})) == 1)
    pg.screenshot(path=f'{SHOTS}/17_dev_billing.png', full_page=True)
    # maintenance check while here
    ev("POS.ACT.devtab('ntc')"); pg.wait_for_timeout(200); ev("POS.ACT.dvmnt('on')"); pg.wait_for_timeout(500)
    ok('maintenance saved', (shop().get('config', {}).get('maint') or {}).get('on') is True)
    signout(); signin('admin')
    ok('admin blocked by maintenance', wait("()=>document.querySelector('#lock .g-ill')&&document.body.classList.contains('gated')&&!document.querySelector('form[data-blform]')", 8000))
    ev("POS.ACT.gout()"); pg.wait_for_timeout(300); devsignin()
    ev("location.hash='#dev'"); pg.wait_for_timeout(200); ev("POS.ACT.devtab('ntc')"); ev("POS.ACT.dvmnt('off')"); pg.wait_for_timeout(400)
    signout(); signin('admin')
    ok('overdue plan locks the admin (soft lock)', wait("()=>document.querySelector('#lock form[data-blform]')", 8000))
    pg.screenshot(path=f'{SHOTS}/18_billing_gate.png', full_page=True)
    pg.fill('#lock [name="ref"]', 'GC-778812'); pg.click('#lock form[data-blform] button[type=submit]'); pg.wait_for_timeout(700)
    pays = shop().get('bill', {}).get('pays', {})
    ok('admin reports the payment from the lock screen', len(pays) == 1 and list(pays.values())[0].get('st') == 'pending', pays)
    ok('admin cannot confirm own payment (rules)', ev(denied(f"await m.update(m.ref({{}}, 'shops/main/bill/pays/{list(pays)[0]}'),{{st:'ok'}})")))
    ev("POS.ACT.gout()"); pg.wait_for_timeout(300); devsignin()
    ev("location.hash='#dev'"); pg.wait_for_timeout(200); ev("POS.ACT.devtab('bill')"); ev("POS.ACT.bltab('pays')"); pg.wait_for_timeout(300)
    pid = list(pays)[0]; ev(f"POS.ACT.blok('{pid}')"); pg.wait_for_timeout(300); ev(f"POS.ACT.blokgo('{pid}')"); pg.wait_for_timeout(600)
    s = shop()
    ok('developer confirms → receipt number + due date moves 1 month', s['bill']['pays'][pid].get('st') == 'ok' and s['bill']['pays'][pid].get('rno') == 'AR-00001' and s['bill']['plan']['due'] > D(-10) and s['billgate']['due'] == s['bill']['plan']['due'], s['bill']['plan'])
    xp = ev(f"(POS.S.cash||[]).find(c=>c.id==='bill-{pid}')") or {}
    ok('confirmed payment auto-logged as a shop expense', xp.get('kind') == 'exp' and xp.get('cat') == 'soft' and xp.get('amt') == 499 and xp.get('method') == 'GCash' and 'AR-00001' in (xp.get('note') or ''), xp)
    ok('expense synced to the cloud', wait(f"()=>{{const d=JSON.parse(localStorage.getItem('__mock_db'));return Object.keys(d.shops.main.d.c.cash||{{}}).some(k=>k.includes('bill-{pid}'))}}", 5000))
    ok('payment flagged for the expense log', s['bill']['pays'][pid].get('xl') is True)
    pg.screenshot(path=f'{SHOTS}/19_dev_payments.png', full_page=True)
    signout(); signin('admin')
    ok('admin gets in after the payment is confirmed', wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='admin'", 8000))
    wait("()=>POS.cloud.state().sync.on", 6000); pg.wait_for_timeout(800)
    ok('admin sees the subscription expense in Expenses', ev(f"(POS.S.cash||[]).filter(c=>c.id==='bill-{pid}').length")==1)
    ev("location.hash='#exp'"); pg.wait_for_timeout(400)
    ok('Expenses page lists Software / Subscription', ev("document.querySelector('#v').textContent.includes('Software / Subscription')"))
    pg.screenshot(path=f'{SHOTS}/20b_admin_expenses.png', full_page=True)
    # safety net: a confirmed payment whose expense was never saved is logged by an admin device (once)
    ev("""()=>{const d=JSON.parse(localStorage.getItem('__mock_db'));d.shops.main.bill.pays.zzpay2={amt:250,date:'%s',meth:'Maya',ref:'MY-1',st:'ok',rno:'AR-00099',cat:new Date(Date.now()-120000).toISOString(),xl:true,by:'u_adm'};localStorage.setItem('__mock_db',JSON.stringify(d));window.dispatchEvent(new StorageEvent('storage',{key:'__mock_db'}))}""" % D(-1))
    ok('admin device logs a missed confirmed payment', wait("()=>(POS.S.cash||[]).some(c=>c.id==='bill-zzpay2'&&c.amt===250)", 8000))
    pg.reload(); wait("()=>!document.body.classList.contains('gated')&&POS.user().role==='admin'", 8000); wait("()=>POS.cloud.state().sync.on", 6000); pg.wait_for_timeout(1500)
    ok('no double logging after reload', ev("(POS.S.cash||[]).filter(c=>String(c.id).startsWith('bill-')).length")==2)
    ev("location.hash='#bill'"); pg.wait_for_timeout(500)
    ok('subscription page shows plan, method and history', ev("(()=>{const t=document.querySelector('#v').textContent;return t.includes('POS Monthly')&&t.includes('0917 123 4567')&&t.includes('GC-778812')})()"))
    ok('history marks payments logged in Expenses', ev("document.querySelectorAll('#v .bl-xl').length")>=1)
    pg.screenshot(path=f'{SHOTS}/20_admin_billing.png', full_page=True)
    signout()

    # ---- developer: screen lock with Quick Log, command palette, Quick Log modal ----
    devsignin()
    ev("POS.ACT.upin()"); pg.wait_for_timeout(300); pg.fill('#pn-a', '4321'); pg.fill('#pn-b', '4321'); ev("POS.ACT.pinsave()"); pg.wait_for_timeout(400)
    ev("POS.ACT.ulock()"); pg.wait_for_timeout(300)
    ok('screen locks', ev("!!document.querySelector('#g-pin')&&document.body.classList.contains('gated')"))
    n0 = ev("POS.S.qlog.length"); pg.click('#lock [data-a="fqllock:1"]'); pg.wait_for_timeout(200)
    pg.fill('.fql-lock [name="t"]', 'Rush: 20 pcs mugs — Joy'); pg.click('.fql-lock .fql-go'); pg.wait_for_timeout(400)
    ok('Quick Log from the lock screen (no unlock)', ev("POS.S.qlog.length")==n0+1 and ev("document.body.classList.contains('gated')"))
    pg.screenshot(path=f'{SHOTS}/21_lock_ql.png')
    pg.fill('#g-pin', '1111'); pg.press('#g-pin', 'Enter'); pg.wait_for_timeout(400)
    ok('wrong screen PIN rejected', ev("document.body.classList.contains('gated')&&!!document.querySelector('.g-err')"))
    pg.fill('#g-pin', '4321'); pg.press('#g-pin', 'Enter'); pg.wait_for_timeout(400)
    ok('right screen PIN unlocks', ev("!document.body.classList.contains('gated')"))
    pg.keyboard.press('Control+k'); pg.wait_for_timeout(250); pg.keyboard.type('liza'); pg.wait_for_timeout(250)
    ok('command palette finds the order', ev("[...document.querySelectorAll('.cmk-i')].some(b=>b.textContent.includes('Tarpaulin'))"))
    pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
    pg.click('body'); pg.keyboard.press('q'); pg.wait_for_timeout(300)
    ok('Q opens Quick Log modal', ev("!!document.querySelector('.mdl [data-qq=\"title\"]')"))
    pg.fill('[data-qq="title"]', 'Wedding invitations 120 pcs'); pg.fill('[data-qq="customer"]', 'Carla'); pg.fill('[data-qq="qty"]', '120'); pg.fill('[data-qq="est"]', '6000')
    ev("POS.ACT.qlqsave()"); pg.wait_for_timeout(300)
    qid = ev("POS.S.qlog.find(x=>x.customer==='Carla').id")
    ev(f"POS.ACT.qlto('order','{qid}')"); pg.wait_for_timeout(400)
    ok('quick log → encoder prefilled', ev("POS.E.customer==='Carla'&&POS.E.items[0].qty==='120'&&location.hash==='#enc'"))
    ev("()=>{POS.E.ptype='full';POS.ACT.stx()}"); pg.wait_for_timeout(400)
    ok('saving the order marks quick log converted', ev(f"POS.S.qlog.find(x=>x.id==='{qid}').status")=='conv')
    ev("location.hash='#qlog'"); pg.wait_for_timeout(300); ev("POS.ACT.qlf('st','all')"); pg.wait_for_timeout(300)
    pg.screenshot(path=f'{SHOTS}/22_qlog_list.png', full_page=True)
    ev("location.hash='#alerts'"); pg.wait_for_timeout(500); pg.screenshot(path=f'{SHOTS}/23_alerts_page.png', full_page=True)
    ok('alerts page renders', ev("!!document.querySelector('.al-list')"))
    b.close()

bad = [e for e in errs if 'favicon' not in e and 'PERMISSION_DENIED' not in e]
print('\nERRORS:', json.dumps(bad, indent=1))
print('SUMMARY', sum(1 for r in results if r[1]), '/', len(results), 'passed')
