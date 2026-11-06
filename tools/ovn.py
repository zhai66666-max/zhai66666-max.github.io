# 美股夜盘/盘前盘后中转：每 60 秒抓一次 Robinhood 公开行情（bounds=24_5 含夜盘），写 ovn.json 推到 live 分支
import json, time, subprocess, urllib.request, os, datetime
SYMS = os.environ.get('SYMS', 'QQQ').split(',')
END = time.time() + float(os.environ.get('RUN_MIN', '57')) * 60
last = None
def get():
    u = 'https://api.robinhood.com/marketdata/quotes/?bounds=24_5&symbols=' + ','.join(SYMS)
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    j = json.load(urllib.request.urlopen(r, timeout=15))
    out = {}
    for q in j.get('results') or []:
        if not q: continue
        px = float(q.get('last_non_reg_trade_price') or q.get('last_extended_hours_trade_price') or q['last_trade_price'])
        prev = float(q.get('adjusted_previous_close') or q['previous_close'])
        reg = float(q['last_trade_price'])
        out[q['symbol']] = {'px': px, 'reg': reg, 'prev': prev, 'pct': round((px / reg - 1) * 100, 3),
                            't': q.get('venue_last_non_reg_trade_time') or q.get('updated_at'),
                            'bid': float(q.get('bid_price') or 0), 'ask': float(q.get('ask_price') or 0)}
    return out
subprocess.run('git config user.name ovn-bot && git config user.email ovn-bot@users.noreply.github.com', shell=True, check=True)
while time.time() < END:
    try:
        d = get()
        key = json.dumps(d, sort_keys=True)
        if d and key != last:
            last = key
            d['_at'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            os.makedirs('/tmp/live', exist_ok=True)
            open('/tmp/live/ovn.json', 'w').write(json.dumps(d, ensure_ascii=False))
            subprocess.run('cd /tmp/live && rm -rf .git && git init -q -b live && git add ovn.json && '
                           'git -c user.name=ovn-bot -c user.email=ovn-bot@users.noreply.github.com commit -qm ovn && '
                           f'git push -qf https://x-access-token:{os.environ["GH_TOKEN"]}@github.com/{os.environ["REPO"]}.git live',
                           shell=True, check=True)
            print(d['_at'], {k: v['px'] for k, v in d.items() if k != '_at'}, flush=True)
    except Exception as e:
        print('err', e, flush=True)
    time.sleep(60)
