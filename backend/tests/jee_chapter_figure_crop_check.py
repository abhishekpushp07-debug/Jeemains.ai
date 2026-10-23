import fitz, json, os
from pathlib import Path
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv(Path(__file__).resolve().parents[1] / '.env')
db=MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]
man=json.load(open('/app/data/jee_chapters/import_manifest.json'))
tot=cut=0; samples=[]; imgs=0
for b in man['books']:
    doc=fitz.open(f"/tmp/jee_chapter_import/{b['subject'].lower()}.pdf")
    for c in b['chapters']:
        s=db.tejas_sets.find_one({'id':c['set_id']},{'questions.q_refs':1,'questions.s_refs':1,'questions.number':1,'key_page':1})
        sp=c['start_page']
        crops={}
        for q in s['questions']:
            for k in ('q_refs','s_refs'):
                for r in q[k]: crops.setdefault(r['page']+sp-1,[]).append((q['number'],k,fitz.Rect(r['rect'])))
        for pn in range(sp, c['end_page']+1):
            page=doc[pn-1]; H=page.rect.height
            objs=[('img',fitz.Rect(i['bbox'])) for i in page.get_image_info()]
            objs+= [('draw',fitz.Rect(d['rect'])) for d in page.get_drawings()]
            imgs+=sum(1 for o in objs if o[0]=='img')
            for kind,r in objs:
                if r.y1<45 or r.y0>H-45: continue   # header/footer rule
                if pn==s['key_page'] and not any(r in cr for _,_,cr in crops.get(pn,[])):
                    # key table rules sit above solution Q1
                    continue
                if pn<sp or not crops.get(pn): continue
                tot+=1
                if not any(cr.contains(r) for _,_,cr in crops[pn]):
                    # allowed: objects before Q1 on chapter intro page
                    if not any(cr.intersects(r) for _,_,cr in crops[pn]) and r.y1 < min(cr.y0 for _,_,cr in crops[pn]): continue
                    cut+=1; samples.append((b['subject'],c['number'],pn,kind,[round(v) for v in r]))
print('objects checked',tot,'images',imgs,'not fully inside a crop',cut); print(samples[:15])
