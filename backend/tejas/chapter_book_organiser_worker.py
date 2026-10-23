"""Bounded chapter-book parser. No solutions generated; source regions are authoritative."""
import codecs
import json
import os
import re
import sys
import fitz
from pdf_organiser_worker import seal, open_pdf, LIMIT
from jee_chapter_parser import parse_jee_book


def page_lines(page):
    return [(line['bbox'], ''.join(s['text'] for s in line['spans']).strip(), bool(line['spans'] and 'Bold' in line['spans'][0]['font']))
            for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]


def whitespace_boundary(page, pix, y):
    # Find an actual full-width inter-question gap, not a math glyph bounding box.
    raw=pix.samples; width=pix.width; left=45; right=min(width-45,560)
    run=0
    for row in range(min(pix.height-1,int(y)), max(50,int(y)-55), -1):
        white=min(raw[row*width+left:row*width+right],default=255)>245
        run=run+1 if white else 0
        if run>=6:
            return float(row+2)
    raise ValueError('Question boundary has no safe whitespace gap; re-export this chapter with more spacing.')


def parse_book(doc):
    cover='\n'.join(doc[i].get_text() for i in range(min(2,len(doc))))
    if 'JEE Main Chapter Tests' in cover:
        return parse_jee_book(doc)
    subjects=[s for s in ('Physics','Chemistry','Mathematics') if re.search(r'(?m)^'+s+r'\s*$',cover)]
    if len(subjects)!=1 or 'BITSAT' not in cover:
        raise ValueError('Use a searchable BITSAT subject chapter book with explicit Chapter headings and answer-key tables.')
    subject=subjects[0]; pages=[p.get_text() for p in doc]
    starts=[]
    for i,text in enumerate(pages):
        m=re.search(r'(?m)^Chapter\s+(\d+)\s*\n(.+?)\n50 questions / Single correct / Four options',text)
        if m: starts.append((i,int(m[1]),m[2].strip()))
    expected=re.search(r'(\d+) chapter units',cover)
    if not starts or len(starts)>60 or [c[1] for c in starts]!=list(range(1,len(starts)+1)) or (expected and int(expected[1])!=len(starts)):
        raise ValueError('Chapter headings/count are incomplete or ambiguous; nothing was published.')
    chapters=[]
    for idx,(start,number,title) in enumerate(starts):
        stop=starts[idx+1][0] if idx+1<len(starts) else len(doc)
        key_pages=[i for i in range(start,stop) if re.search(r'(?m)^Answer key\s*$',pages[i])]
        if len(key_pages)!=1: raise ValueError(f'Chapter {number}: exactly one answer-key page is required.')
        kp=key_pages[0]; key_text=pages[kp]
        if title not in key_text: raise ValueError(f'Chapter {number}: key page title does not match.')
        keys={}; key_refs={}
        # Pass1: extraction reading order.
        for m in re.finditer(r'(?m)^(\d{2})\s*\n([A-D])\s*$',key_text):
            qn=int(m[1])
            if qn in keys: raise ValueError(f'Chapter {number}: duplicate key Q{qn}.')
            keys[qn]=m[2]
        if sorted(keys)!=list(range(1,51)): raise ValueError(f'Chapter {number}: missing/ambiguous answer keys.')
        # Pass2: independent geometric neighbour check (never reuses pass1 ordering).
        words=doc[kp].get_text('words'); spatial={}
        for w in words:
            if not re.fullmatch(r'\d{2}',w[4]) or not 1<=int(w[4])<=50 or not 180<w[1]<doc[kp].rect.height-80: continue
            candidates=[v for v in words if v[4] in ('A','B','C','D') and 0<v[0]-w[2]<65 and abs(v[1]-w[1])<2]
            if len(candidates)!=1: raise ValueError(f'Chapter {number}: key geometry is ambiguous.')
            v=candidates[0]; qn=int(w[4]); spatial[qn]=v[4]
            key_refs[qn]={'page':kp+1,'rect':[round(w[0]-4,2),round(min(w[1],v[1])-4,2),round(v[2]+4,2),round(max(w[3],v[3])+4,2)]}
        if spatial!=keys: raise ValueError(f'Chapter {number}: two independent key reads disagree.')
        anchors=[]; pixmaps={}
        for pi in range(start,kp):
            page=doc[pi]
            for box,text,bold in page_lines(page):
                m=re.match(r'^(\d{2})\.(?:\s|$)',text)
                if m and bold and 45<=box[0]<=65 and box[1]>55:
                    if pi not in pixmaps: pixmaps[pi]=page.get_pixmap(colorspace=fitz.csGRAY)
                    anchors.append({'number':int(m[1]),'page':pi,'top':whitespace_boundary(page,pixmaps[pi],box[1])})
        if [a['number'] for a in anchors]!=list(range(1,51)):
            raise ValueError(f'Chapter {number}: expected exact question sequence1–50; found {len(anchors)} anchors.')
        questions=[]
        for n,a in enumerate(anchors):
            end=anchors[n+1] if n+1<len(anchors) else {'page':kp,'top':55}
            refs=[]; texts=[]
            for pi in range(a['page'],min(end['page']+1,kp)):
                page=doc[pi]; top=a['top'] if pi==a['page'] else 55
                bottom=end['top'] if pi==end['page'] else page.rect.height-45
                if bottom<=top+2: continue
                rect=fitz.Rect(45,top,page.rect.width-45,bottom)
                text=page.get_text(clip=rect).strip()
                if not text: continue
                pix=pixmaps.get(pi) or page.get_pixmap(colorspace=fitz.csGRAY)
                raw=pix.samples; last=None
                for row in range(min(pix.height-1,int(bottom)-1),int(top),-1):
                    if min(raw[row*pix.width+45:row*pix.width+int(page.rect.width)-45],default=255)<230:
                        last=row; break
                if last is not None: rect.y1=min(bottom,last+6)
                refs.append({'page':pi+1,'rect':[round(v,2) for v in rect]});texts.append(page.get_text(clip=rect).strip())
            text='\n'.join(texts)
            if not 1<=len(refs)<=3 or len(text)>16000 or set(re.findall(r'\(([A-D])\)',text))!=set('ABCD'):
                raise ValueError(f'Chapter {number} Q{a["number"]}: incomplete options or unsafe source regions.')
            questions.append({'number':a['number'],'subject':subject,'section':title,'topic':title,'type':'mcq',
                'text':text,'options':{k:'See original option '+k for k in 'ABCD'},'answer':keys[a['number']],
                'solution':f'Supplied answer key: {keys[a["number"]]}. This book does not contain a worked solution.',
                'solution_number':a['number'],'render_mode':'source','solution_kind':'answer_key_only',
                'accessible_text':'Original PDF question and four options. Formula-safe image; machine text is not a verified accessible transcription.',
                'solution_accessible_text':f'Supplied key {keys[a["number"]]}; no worked solution provided.',
                'q_refs':refs,'s_refs':[key_refs[a['number']]],'approved':False,'issues':[]})
        chapters.append({'number':number,'title':title,'start_page':start+1,'end_page':kp,'key_page':kp+1,
                         'questions':questions,'verification':{'questions':50,'keys':50,'options':50,'key_checks_agree':True,'source_images':True}})
    return {'subject':subject,'chapters':chapters,'pages':len(doc),'count':sum(len(c['questions']) for c in chapters),
            'sandbox':'chroot_low_uid_seccomp_resource_limits','parser_version':'chapter50-v1'}


def main():
    try:
        directory=sys.argv[1]
        with open(os.path.join(directory,'questions.pdf'),'rb') as f: raw=f.read(LIMIT+1)
        codecs.lookup('raw_unicode_escape');codecs.lookup('unicode_escape');json.dumps({'x':'अ'}).encode()
        seal(directory)
        if not raw.startswith(b'%PDF-') or len(raw)>LIMIT: raise ValueError('Use a valid chapter PDF under50MB.')
        doc=fitz.open(stream=raw,filetype='pdf')
        if doc.is_encrypted or not 1<=len(doc)<=1000 or any(p.rect.width>2000 or p.rect.height>2000 for p in doc):
            raise ValueError('Use an unlocked chapter book of at most1000standard-size pages.')
        result=parse_book(doc)
        encoded=json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()
        if len(encoded)>12*1024*1024: raise ValueError('Book output exceeds safe bounds. Split the source.')
        sys.stdout.buffer.write(encoded)
    except ValueError as exc:
        sys.stdout.write(json.dumps({'error':str(exc)[:450]}));sys.exit(2)
    except Exception:
        sys.stdout.write(json.dumps({'error':'Chapter book could not be read safely. Use a searchable supported chapter book.'}));sys.exit(3)

if __name__=='__main__': main()
