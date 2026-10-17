import requests,time,sys
API=open('/app/frontend/.env').read().split('REACT_APP_BACKEND_URL=')[1].split()[0]
B=API+'/api'; s=requests.Session(); s.headers['Origin']=API
s.post(B+'/auth/phone',json={'phone':sys.argv[1]}); aid=sys.argv[2]
j=s.post(B+f'/attempts/{aid}/report',json={}).json()['data']
for i in range(80):
  x=s.get(B+f"/jobs/{j['id']}")
  if x.status_code!=200: time.sleep(3); continue
  j=x.json()["data"]
  if j['status'] in ('done','failed'): break
  time.sleep(3)
print(j['status'], j.get('message'), j.get('error'))
r=s.get(B+f'/jobs/{j["id"]}/download'); print(r.status_code, len(r.content)); open('/app/test_reports/mock_report_ai.pdf','wb').write(r.content)
