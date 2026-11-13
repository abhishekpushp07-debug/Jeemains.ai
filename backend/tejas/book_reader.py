import re
from .book_models import Region, PageMap
from .pdf_organiser_worker import ANCHOR, SUBJECT, KEY, choose_options

MOCK=re.compile(r'^(?:(?:full[ -]length|practice|mock|model|sample)\s+)*(?:test|mock|paper)\s*(?:no\.?\s*)?[#:\-]?\s*(\d{1,3})\b',re.I)
ROLE=re.compile(r'(?:(?:detailed|worked|hints?\s*(?:&|and))\s+)?(solutions?|answers?\s*keys?|answers?)(?:\s*(?:[:\-\u2013\u2014]|for|to|of)?\s*(?:(?:mock|practice|model|sample)?\s*(?:test|mock|paper)\s*(?:no\.?\s*)?\d{1,3}|physics|chemistry|math(?:ematic)?s|biology|english|logical\s+reasoning))?\s*[:.]?',re.I)


def read_page(lines, previous, geometry=()):
    context=dict(previous); regions=[]; issues=[]
    text='\n'.join(x['text'] for x in lines)
    if not lines:
        return PageMap(issues=['Scanned or empty page: approve AI reading or map the original page manually.']),context
    headers=[]; anchors=[]
    for line in lines:
        value=line['text'];m=MOCK.match(value);role=ROLE.fullmatch(value.strip())
        if m:
            label='Mock '+str(int(m[1])); headers.append((line['rect'][1], 'mock',label))
            starts_questions=bool(re.search(r'\b(?:instructions|duration|total questions)\b',text,re.I) or choose_options(text)[0])
            if context.get('role') in ('key','solution') and not starts_questions:
                issues.append('Mock heading follows keys/solutions without question instructions: confirm the section type.')
        if role and len(value)<140:
            headers.append((line['rect'][1],'role','solution' if 'solution' in role[1].lower() else 'key'))
        subject=SUBJECT.match(value)
        if subject and len(value)<90: headers.append((line['rect'][1],'subject',subject[1].title().replace('Maths','Mathematics')))
        a=ANCHOR.match(value)
        if a and (line['rect'][0]<.27 or .46<line['rect'][0]<.68):
            anchors.append((line,a))
    two=any(x[0]['rect'][0]>.46 for x in anchors) and any(x[0]['rect'][0]<.3 for x in anchors)
    if two:
        issues.append('Two-column layout: confirm column boundaries and continuation regions in the review desk.')
    top_headers=sorted(h for h in headers if not anchors or h[0]<=min(a[0]['rect'][1] for a in anchors))
    for _,kind,value in top_headers:
        if kind=='mock': context.update(mock=value,role='question')
        else: context[kind]=value
    if len({h[2] for h in headers if h[1]=='mock'})>1:
        issues.append('Multiple mock headings share this page; map their regions explicitly.')
    if not anchors:
        classification='instructions' if headers or re.search(r'\b(duration|instructions|marking)\b',text,re.I) else 'unresolved'
        if re.search(r'^\s*(contents|index)\b',text,re.I): classification='contents'
        if classification=='unresolved':issues.append('No reliable question or key anchors; classify or attach this continuation.')
        regions=[Region(role='instructions' if classification=='instructions' else 'ignore',mock=context.get('mock',''),rect=[.01,.01,.99,.99],text=text[:30000],checked=classification in ('instructions','contents'))]
        return PageMap(classification=classification,regions=regions,issues=issues),context
    anchors.sort(key=lambda a:(int(two and a[0]['rect'][0]>.46),a[0]['rect'][1]))
    for i,(line,a) in enumerate(anchors):
        col=int(two and line['rect'][0]>.46); top=max(.005,line['rect'][1]-.004)
        local=dict(context)
        for y,kind,value in sorted(headers):
            if y<=top+.006:
                if kind=='mock':local.update(mock=value,role='question')
                else:local[kind]=value
        end=next((z[0]['rect'][1]-.004 for z in anchors[i+1:] if int(two and z[0]['rect'][0]>.46)==col),.97)
        breaks=[h[0]-.004 for h in headers if top+.01<h[0]<end]
        if breaks:end=min(breaks)
        if end<=top:continue
        rect=[.02 if col==0 else .5,top,.49 if two and col==0 else .98,end]
        for box in [x['rect'] for x in lines]+list(geometry):
            intersects=min(rect[2],box[2])-max(rect[0],box[0])>.002 and min(rect[3],box[3])-max(rect[1],box[1])>.002
            contained=rect[0]-.002<=box[0] and rect[1]-.002<=box[1] and box[2]<=rect[2]+.002 and box[3]<=rect[3]+.002
            if intersects and not contained:
                issues.append(f'Q{a[1] or a[2]}: crop boundary crosses text or a diagram; adjust the region.')
                break
        contained=[x['text'] for x in lines if rect[0]-.01<=x['rect'][0]<rect[2] and top<=x['rect'][1]<end]
        value='\n'.join(contained);role=local.get('role','question')
        family,_,ambiguous=choose_options(value)
        keys={m[1].upper() for m in KEY.finditer(value)}
        if role=='key':
            tail=a[3].strip(); bare=re.fullmatch(r'[\[(]?([A-D]|[+\-]?\d{1,20})[\])]?',tail,re.I)
            if bare:keys.add(bare[1].upper())
        if len(keys)>1: issues.append(f'Conflicting printed keys near Q{a[1] or a[2]}.')
        if role=='question' and keys:issues.append(f'Answer visible near Q{a[1] or a[2]}; separate it from the question crop.')
        if not local.get('mock'):issues.append('Mock identity needs an explicit heading or owner mapping.')
        if not local.get('subject'):issues.append('Subject/section identity needs confirmation.')
        if role=='question' and not family: issues.append(f'Q{a[1] or a[2]}: confirm response type, options and continuation.')
        if role=='solution' and not a[1]:issues.append('Bare solution numbers may be numbered steps; confirm anchors.')
        regions.append(Region(role=role,mock=local.get('mock',''),subject=local.get('subject',''),section=local.get('subject',''),
            number=int(a[1] or a[2]),rect=rect,text=value[:30000],answer=next(iter(keys)) if len(keys)==1 else '',
            option_labels=list(family),response_type='mcq' if family else 'unresolved',checked=not two and not ambiguous and bool(a[1])))
    before=min(a[0]['rect'][1] for a in anchors)
    intro='\n'.join(x['text'] for x in lines if x['rect'][1]<before)
    if intro.strip():
        allowed=r'^(?:jee|bitsat|comedk|mock|practice|test|paper|time|duration|questions|total|correct|incorrect|wrong|unanswered|skipped|all\s+questions|instructions|physics|chemistry|math|solutions?|answers?|no\s+worked|page|english|logical|numerical|section)\b'
        if any(not re.search(allowed,line.strip(),re.I) for line in intro.splitlines() if len(line.strip())>3):
            issues.append('Leading content may continue a previous question or solution. Attach it explicitly instead of discarding it as instructions.')
        regions.insert(0,Region(role='instructions',mock=context.get('mock',''),rect=[.01,.001,.99,max(.002,before-.005)],text=intro[:30000],checked=True))
    context=local
    roles={r.role for r in regions if r.role not in ('instructions','ignore')}
    classification={'question':'questions','key':'answer_key','solution':'solutions'}.get(next(iter(roles)),'mixed') if len(roles)==1 else 'mixed'
    return PageMap(classification=classification,regions=regions,issues=list(dict.fromkeys(issues))),context


def infer_rules(text):
    def match(pattern):return re.search(pattern,text,re.I)
    duration=match(r'(?:duration|time(?:\s+allowed)?)\s*[:=]\s*(\d+)\s*(minutes?|mins?|hours?|hrs?)')
    count=match(r'(?:total\s+(?:number\s+of\s+)?questions|questions)\s*[:=]\s*(\d+)')
    correct=match(r'(?:correct(?:\s+answer)?)\s*[:=]\s*\+?(\d+(?:\.\d+)?)')
    wrong=match(r'(?:wrong|incorrect)(?:\s+answer)?\s*[:=]\s*(-?\d+(?:\.\d+)?)')
    skipped=match(r'(?:unanswered|skipped)\s*[:=]\s*0\b')
    exam=next((x for x in ('JEE Main','BITSAT','COMEDK') if x.lower() in text.lower()),None)
    compulsory=bool(match(r'all\s+questions\s+(?:are\s+)?compulsory'))
    unsupported=bool(match(r'\b(optional|attempt\s+any|bonus|round(?:ing|ed)|decimal|multiple\s+correct)\b'))
    correct_values=set(re.findall(r'(?<!in)\bcorrect(?:\s+answer)?\s*[:=]\s*\+?(\d+(?:\.\d+)?)',text,re.I))
    wrong_values=set(re.findall(r'\b(?:wrong|incorrect)(?:\s+answer)?\s*[:=]\s*(-?\d+(?:\.\d+)?)',text,re.I))
    if len(correct_values)>1 or len(wrong_values)>1:return {}
    if not all((duration,count,correct,wrong,skipped,exam,compulsory)) or unsupported:return {}
    return {'exam':exam,'minutes':int(duration[1])*(60 if duration[2].lower().startswith('h') else 1),'expected_questions':int(count[1]),
        'correct':float(correct[1]),'wrong':-abs(float(wrong[1])),'skipped':0,'mechanic':'all_compulsory','bonus_count':0,
        'first_number':1,'numbering':'continuous','solution_policy':'key_only' if match(r'no\s+worked\s+solutions|answer\s+key\s+only') else 'original_expected',
        'key_only':[],'unsupported':'','note':'Explicit printed instructions; no examination preset inferred.'}
