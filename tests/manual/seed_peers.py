import requests,uuid,time,random,sys
API=open('/app/frontend/.env').read().split('REACT_APP_BACKEND_URL=')[1].split()[0]
B=API+'/api'
def run(phone,acc,frac,bonus):
    s=requests.Session(); s.headers['Origin']=API
    s.post(B+'/auth/phone',json={'phone':phone})
    sid=s.get(B+'/exam-navigation/bitsat/catalogue?kind=mocks').json()['data']['items'][0]['id']
    s.post(B+f'/sets/{sid}/preflight',json={})
    a=s.post(B+f'/sets/{sid}/start',json={'start_key':str(uuid.uuid4()),'device_checked':True}).json()['data']
    keys={}
    main=[q for q in a['questions'] if not q['bonus']]
    for q in main:
        if random.random()>frac and not bonus: continue
        s.put(B+f'/attempts/{a["id"]}/answers/{q["id"]}',json={'value':random.choice('ABCD'),'revision':1,'request_id':str(uuid.uuid4())})
    if bonus:
        s.post(B+f'/attempts/{a["id"]}/bonus',json={})
        for q in [q for q in a['questions'] if q['bonus']][:6]:
            s.put(B+f'/attempts/{a["id"]}/answers/{q["id"]}',json={'value':random.choice('ABCD'),'revision':1,'request_id':str(uuid.uuid4())})
    s.post(B+f'/attempts/{a["id"]}/submit',json={})
    return a['id']
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 1)
for i in range(6):
    print(run(f'+9199000002{i:02d}',0,random.choice([.4,.6,.8]),i==0))
