import requests
API=open('/app/frontend/.env').read().split('REACT_APP_BACKEND_URL=')[1].split()[0]
B=API+'/api'; s=requests.Session(); s.headers['Origin']=API
print(s.post(B+'/auth/login',json={'email':'abhishek@billpe.com','password':'55241878'}).status_code)
d=s.get(B+'/studio/ai-review?state=all').json(); d=d.get('data',d)
print(d['counts'], d['progress'], len(d['items']))
for x in d['items'][:3]: print(x['set_title'], x['number'], x['key'], x['ai_answer'], x['insight'][:160])
