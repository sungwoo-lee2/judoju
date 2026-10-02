from __future__ import annotations
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from krx_api import snapshot as get_snapshot, scan as live_scan, diagnostics as diagnose_connections
from storage import storage_status
from ai_service import ai_status, market_scan

BASE = Path(__file__).resolve().parent
app = FastAPI(title='Leader Finder v11', version='11.0')
app.mount('/static', StaticFiles(directory=str(BASE/'static')), name='static')
templates = Jinja2Templates(directory=str(BASE/'templates'))

@app.on_event('startup')
def startup_refresh():
    # Keep default startup fast/stable on Render. Set AUTO_REFRESH=1 to fetch live KRX data on boot.
    if os.getenv('AUTO_REFRESH','0') == '1':
        try:
            live_scan(int(os.getenv('UNIVERSE_SIZE','80')))
        except Exception:
            pass
    else:
        get_snapshot()

@app.get('/', response_class=HTMLResponse)
def home(request: Request):
    snap = get_snapshot()
    return templates.TemplateResponse('index.html', {'request':request, 'snap':snap})


@app.get('/healthz')
def healthz():
    status = storage_status()
    snap = get_snapshot()
    return {
        'ok': True,
        'app': 'leader-finder-v11',
        'ai': ai_status(),
        'storage': status,
        'source': snap.get('source'),
        'leader_count': len(snap.get('items', [])),
        'early_leader_count': len(snap.get('early_leaders', [])),
    }


@app.get('/api/diagnostics')
def diagnostics():
    return diagnose_connections()


@app.get('/api/ai-status')
def get_ai_status():
    return ai_status()

@app.post('/api/ai-market-scan')
def ai_market_scan():
    try:
        return {'ok': True, **market_scan()}
    except Exception as e:
        return {'ok': False, 'error': str(e), **ai_status()}

@app.get('/api/storage-status')
def get_storage_status():
    return storage_status()

@app.get('/api/snapshot')
def snapshot():
    return get_snapshot()

@app.post('/api/refresh')
def refresh():
    try:
        return {'ok':True, **live_scan(int(os.getenv('UNIVERSE_SIZE','80')))}
    except Exception as e:
        fallback = get_snapshot()
        return {'ok':False, 'error':str(e), **fallback}

@app.get('/api/leaders')
def leaders():
    s=get_snapshot(); return {'items':s.get('items',[]), 'source':s.get('source')}

@app.get('/api/sectors')
def sectors():
    s=get_snapshot()
    if 'sectors' in s: return {'items':s['sectors'], 'source':s.get('source')}
    # old snapshot compatibility
    return {'items':[], 'source':s.get('source')}


@app.get('/api/lifecycle')
def lifecycle():
    s=get_snapshot(); return {'items':s.get('lifecycle',[]), 'source':s.get('source')}

@app.get('/api/pullbacks')
def pullbacks():
    s=get_snapshot(); return {'items':s.get('pullbacks',[]), 'source':s.get('source')}

@app.get('/api/rotations')
def rotations():
    s=get_snapshot(); return {'items':s.get('rotations',[]), 'source':s.get('source')}

@app.get('/api/performance')
def performance():
    s=get_snapshot(); return s.get('performance',{})

@app.get('/api/early-leaders')
def early_leaders():
    s=get_snapshot(); return {'items':s.get('early_leaders',[]), 'source':s.get('source')}

@app.get('/api/stock/{ticker}')
def stock(ticker: str):
    s=get_snapshot()
    item=next((x for x in s.get('items',[]) if x['ticker']==ticker), None) or next((x for x in s.get('early_leaders',[]) if x['ticker']==ticker), None)
    return {'item':item}
