# Browser-only read-only API fixtures for Home visual QA (iteration 149). Paste into browser_automation.
import json
BASE='https://campus-search-debug.preview.emergentagent.com'
writes=[]
GUEST={'v':False}
async def handler(route):
    req=route.request; u=req.url.split('?')[0]
    if req.method not in ('GET','HEAD','OPTIONS'):
        writes.append(req.method+' '+u); await route.fulfill(status=403,content_type='application/json',body='{"detail":"blocked"}'); return
    if u.endswith('/auth/session'): body={"user":None} if GUEST['v'] else {"user":{"id":"visual-home149","name":"Visual check","role":"student","access_type":"unverified_phone","phone_last4":"0000"}}
    elif u.endswith('/series/all-india-jee/streak'): body={"user_id":"visual-home149","stage":"prelaunch","completed_count":0,"current_streak":0,"best_streak":0,"milestones":[],"days":[],"today_state":"prelaunch","next_milestone":None,"policy":"fixture"}
    elif u.endswith('/series/all-india-jee'): body={"server_now":1790000000,"today":"2026-10-26","first_date":"2026-12-01","last_date":"2027-01-31","today_slot":None,"slots":[]}
    else: body={}
    await route.fulfill(status=200,content_type='application/json',body=json.dumps(body))
