import asyncio,sys,traceback
sys.path.insert(0,'/app/backend')
from dotenv import load_dotenv; load_dotenv('/app/backend/.env')
from tejas.db import attempts,files,get
from tejas.corrections import with_grade
from tejas.mock_solutions import for_questions
from tejas_storage import get_object
from tejas import reports
async def main(aid):
    a=await with_grade(await get(attempts,aid),'original')
    a['ai_solutions']={k:v['solution'] for k,v in (await for_questions(a['questions'])).items() if v.get('state')=='ready'}
    src={}
    for fid in {r['file_id'] for q in a['questions'] for r in q.get('q_refs',[])}: src[fid]=get_object((await get(files,fid))['path'])
    orig=reports.Report.text
    def text(self,t,*args,**kw):
        try: return orig(self,t,*args,**kw)
        except ValueError: print('FAILED TEXT', repr(str(t)[:300]), len(str(t)), str(t).count('\n')); raise
    reports.Report.text=text
    try:
        pdf=reports.render_report(a,lambda f:src[f]); print('ok',len(pdf))
    except Exception: traceback.print_exc(limit=2)
asyncio.run(main(sys.argv[1]))
