import sys, copy; sys.argv=['x','/tmp/neg.json']
sys.path.insert(0,'/app/backend/tests'); sys.path.insert(0,'/app/backend')
import jee_chapter_source_audit as A
orig=A.db.tejas_sets.find_one
class W:
    def __init__(s,c): s.c=c
    def find_one(s,q,p=None):
        d=orig(q,p)
        if d and d.get('chapter_number')==1:
            d=copy.deepcopy(d); subj=d['chapter_subject']
            if subj=='Physics': d['questions'][4]['answer']='A' if d['questions'][4]['answer']!='A' else 'B'
            if subj=='Mathematics': d['questions'][9]['q_refs'][0]['rect'][3]-=40
            if subj=='Chemistry': d['rules']['minutes']=40
        return d
class DB:
    def __getattr__(s,n): return W(None) if n=='tejas_sets' else getattr(A.MongoClient,'x',None) or getattr(real,n)
real=A.db; A.db=DB()
A.main()
