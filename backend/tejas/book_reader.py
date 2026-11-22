import re
from .book_models import Region, PageMap
from .pdf_organiser_worker import ANCHOR, SUBJECT, choose_options
from .chapter_reader import find as chapter_marks, exercise, norm

READER_VERSION=7
MOCK=re.compile(r'^(?:(?:jee\s*main|jee|bitsat|comedk)\s+)?(?:(?:full[ -]length|practice|mock|model|sample)\s+)*(?:test|mock|paper)\s*(?:no\.?\s*)?[#:\-]?\s*(\d{1,3})\b',re.I)
ROLE=re.compile(r'(?:(?:detailed|worked|hints?\s*(?:&|and))\s+)?(solutions?|answers?\s*keys?|answers?)(?:\s*(?:[:\-\u2013\u2014]|for|to|of)?\s*(?:(?:mock|practice|model|sample)?\s*(?:test|mock|paper)\s*(?:no\.?\s*)?\d{1,3}|physics|chemistry|math(?:ematic)?s|biology|english|logical\s+reasoning))?\s*[:.]?',re.I)
BARE=re.compile(r'^(?:(Q)(?:uestion)?\.?\s*)?(\d{1,3})\s*[.):]$',re.I)
PASSAGE=re.compile(r'^read\s+the\s+(?:following\s+)?(?:passage|paragraph|comprehension|text)\b.*?\bquestions?\s+(\d{1,3})(?:\s*(?:[\u2013\u2014\-]|to|and)\s*(\d{1,3}))?',re.I)
SECTION=re.compile(r'^section\s*[- ]?([ab])\b',re.I)
NUMERIC_HEAD=re.compile(r'^(?:numerical|integer)\b[\w\s()/,-]{0,50}$',re.I)
NUMERIC=re.compile(r'\b(?:numerical|integer[- ]type|integer\s+answers?|numeric(?:al)?\s+value)\b',re.I)
PRINTED=re.compile(r'^\s*(?i:answer|ans\.?|correct\s+(?:option|answer))\s*[:=]\s*[\[(]?\s*([A-D]|[+\-\u2212]?\d{1,20})\b',re.M)
INTRO_OK=re.compile(r'\b(?:instructions?|duration|time\s*:|marking|bonus\s+section|answer\s+keys?|questions?\s+only)\b',re.I)
CELL_NUMBER=re.compile(r'\d{1,3}')
CELL_KEY=re.compile(r'\(?[A-D]\)?|[+\-\u2212]?\d{1,20}')
# A printed key needs 'is', ':' or a bracket after the cue, so prose such as 'could then answer a different' is not a key.
ANSWER_NEAR=re.compile(r'\b(?:[Aa]nswer|ANSWER|Ans\.?|[Cc]orrect[ \t]+(?:option|answer))[ \t]*(?:(?:is[ \t]+|[:=\-][ \t]*)[\[(]?|[\[(])[ \t]*([A-D](?![A-Za-z])|[+\-]?\d+(?![\d.]))')
# An answer-entry line printed under a numerical question ('Numerical response ____'); it is not a section heading.
ENTRY=re.compile(r'^(?:numerical|numeric|integer)\s+(?:response|answer|value|entry)\s*[:\-]?[\s_.]*$',re.I)
# A group label printed between questions, ending with the questions it announces: 'Two chapters (Q31–Q50)'.
GROUP=re.compile(r'\(\s*Q\.?\s*(\d{1,3})\s*[\u2013\u2014\-]\s*Q?\.?\s*\d{1,3}\s*\)\s*$',re.I)
TOP,BOTTOM=.06,.94
# Big bracket pieces (⎛ ⎜ ⎝, private-use TeX extension glyphs, or fonts mapping them to '"' and '#') printed as their own spans.
DELIMITER=re.compile(r'[\uf8e0-\uf8ff\u239b-\u23ad()\[\]{}|"#]+')


def mock_title(value):
    """'Mock 26' / 'JEE Main Practice Mock 27' headings; prose such as 'Test 0.0500 M directly…' is not a title."""
    m=MOCK.match(value)
    return m if m and value[:1].isupper() and len(value)<60 and int(m[1])>=1 else None


CRUMB=re.compile(r'\s+[/|\u2022\u00b7]\s+')
CORRECT=re.compile(r'(?:single|multiple)[- ]correct(?:\s+(?:mcqs?|questions?|options?))?|mcqs?',re.I)


def subject_of(part):
    m=SUBJECT.match(part)
    return m[1].title().replace('Maths','Mathematics') if m and m.end()==len(part) else None


def crumbs(value):
    """A running label made only of parts such as 'MOCK 01 / Mathematics / Single-correct MCQ' or 'MATHEMATICS / DETAILED SOLUTION':
    (mock, subject, role match, numeric), or None when any part is something else."""
    parts=[p.strip() for p in CRUMB.split(value) if p.strip()]
    if len(parts)<2 or len(value)>120:return None
    mock=subject=role=numeric=None
    for p in parts:
        m=mock_title(p)
        if m and m.end()==len(p):mock='Mock '+str(int(m[1]))
        elif subject_of(p):subject=subject_of(p)
        elif p[:1].isupper() and ROLE.fullmatch(p):role=ROLE.fullmatch(p)
        elif CORRECT.fullmatch(p):numeric=False
        elif NUMERIC.search(p):numeric=True
        else:return None
    return mock,subject,role,numeric


def role_of(value):
    """'Answer key', 'Mock 01 answer key', or the role part of a running label."""
    if not value[:1].isupper():return None
    if r:=ROLE.fullmatch(value):return r
    m=mock_title(value)
    if m and (rest:=value[m.end():].strip(' :-\u2013\u2014')) and (r:=ROLE.fullmatch(rest)):return r
    c=crumbs(value)
    return c[2] if c else None


def band(line):
    """Running header/footer: short lines in the top or bottom page margin."""
    if line.get('body'):return False
    _,y0,_,y1=line['rect'];text=line['text'].strip()
    return (y1<=TOP and len(text)<60) or (y0>=BOTTOM and len(text)<90)


def anchor_of(line):
    """(number, has_q_prefix, printed_alone) for a question/key/solution start."""
    value=line['text'].strip();bare=BARE.match(value)
    a=None if bare or not re.match(r'^(?:Q(?:uestion)?\.?\s*\d{1,3}|\d{1,3}[.)]\s)',value,re.I) else ANCHOR.match(value)
    found=(int(bare[2]),bool(bare[1]),True) if bare else (int(a[1] or a[2]),bool(a[1]),False) if a else None
    # 'Q10', 'Q2 = 1' or 'q2/q1)' inside working are symbols, not 'Question 10' / 'Q10.' headings.
    if found and found[1] and not re.match(r'^(?:Question|QUESTION)\s*\d{1,3}\b|^Q\.?\s*\d{1,3}\s*[.):\]](?!\d)',value):return None
    return found if found and 1<=found[0]<=600 else None


QCELL=re.compile(r'Q\.?\s*\d{1,3}')
ANSWERED=re.compile(r'^\s*\d{1,3}[.)]\s*(?:Answer|ANSWER|Ans\.?|ANS\.?|Solution|SOLUTION)\s*[:\-]?\s*\((?:[A-D]|[+\-\u2212]?\d{1,9}(?:\.\d+)?)\)')


def cell_no(text):
    return int(re.sub(r'\D','',text))


def cell_pair(q, k):
    return (cell_no(q['text']),k['text'].strip().strip('()').replace('\u2212','-').upper(),[q['rect'][0],min(q['rect'][1],k['rect'][1]),k['rect'][2],max(q['rect'][3],k['rect'][3])])


def key_cells(body,least=10,ruled=False):
    """Answer-key tables printed as Q | Key cell pairs (a source column may sit between them), read row by row.
    ruled=True also reads ruled tables whose numbers ('12' or 'Q12') sit far from their keys; ruled='only' reads nothing else."""
    number=lambda t:CELL_NUMBER.fullmatch(t) or (ruled and QCELL.fullmatch(t))
    cells=sorted((x for x in body if number(x['text'].strip()) or CELL_KEY.fullmatch(x['text'].strip())),key=lambda x:(x['rect'][1]+x['rect'][3])/2)
    rows=[]
    for c in cells:
        mid=(c['rect'][1]+c['rect'][3])/2
        if rows and abs(mid-rows[-1][0])<.006:rows[-1][1].append(c)
        else:rows.append((mid,[c]))
    wide={}
    for _,row in rows:row.sort(key=lambda x:x['rect'][0])
    for _,row in rows if ruled else []:
        for q,k in zip(row,row[1:]):
            if number(q['text'].strip()) and CELL_KEY.fullmatch(k['text'].strip()) and .15<=k['rect'][0]-q['rect'][2]<(.45 if ruled=='only' else .32) and 1<=cell_no(q['text'])<=600:
                wide.setdefault((round(q['rect'][0],2),round(k['rect'][2],2)),[]).append((q,k))
    found=[]
    for column in wide.values():
        # A ruled key table prints its numbers and keys far apart: a whole column of consecutive numbers at the same two edges is one.
        numbers=[cell_no(q['text']) for q,_ in sorted(column,key=lambda c:c[0]['rect'][1])]
        if len(column)>=(5 if ruled=='only' else 10) and numbers==list(range(numbers[0],numbers[0]+len(numbers))):found+=[cell_pair(q,k) for q,k in column]
    if len(found)>=least and len({p[0] for p in found})==len(found):return found
    if ruled=='only':return []
    pairs=[]
    for _,row in rows:
        i=0
        while i+1<len(row):
            q,k=row[i],row[i+1]
            gap=k['rect'][0]-q['rect'][2]
            # A wider gap is one table row only when another cell (such as the question's source) is printed inside it.
            between=.15<=gap<.32 and any(x is not q and x is not k and q['rect'][2]<=x['rect'][0] and x['rect'][2]<=k['rect'][0] and abs((x['rect'][1]+x['rect'][3])/2-(q['rect'][1]+q['rect'][3])/2)<.006 for x in body)
            if CELL_NUMBER.fullmatch(q['text'].strip()) and CELL_KEY.fullmatch(k['text'].strip()) and (0<gap<.15 or between) and 1<=int(q['text'])<=600:
                pairs.append(cell_pair(q,k));i+=2
            else:i+=1
    return pairs if len(pairs)>=least and len({p[0] for p in pairs})==len(pairs) else []


def pad(rect):
    return [max(0,rect[0]-.006),max(0,rect[1]-.004),min(1,rect[2]+.006),min(1,rect[3]+.004)]


def row_top(line, boxes, delimiters=frozenset()):
    """Top of the printed row an anchor starts, including tall formulas set on that same row.
    A raised glyph joins the row only if it overlaps the row more than the content printed above it
    (an integral's lower limit from the previous option stays with that option); bracket pieces of a
    matrix on the row are never 'content above'."""
    x0,y0,_,y1=line['rect'];top=y0
    def own(b,top):
        mine=min(b[3],y1)-max(b[1],top)
        # Only content that ends above the anchor row counts as 'above'; a matrix bracket on the row itself does not.
        above=max([min(b[3],o[3])-max(b[1],o[1]) for o in boxes if o is not b and id(o) not in delimiters and o[1]<b[1]-.002 and o[3]<=y0-.001 and o[3]-o[1]<.05 and min(b[2],o[2])-max(b[0],o[0])>-.05]+[0])
        return mine>=above
    for _ in range(4):
        grown=min([top]+[b[1] for b in boxes if b[0]>x0+.01 and b[1]>=y0-.03 and b[3]-b[1]<.05 and b[1]<y1 and b[3]>top+.001 and own(b,top)])
        if grown>=top:break
        top=grown
    return top


def in_sequence(anchors, last, resets=()):
    """Drop wrapped text such as '3. Find…' or formula pieces like '2)' that break the printed question sequence.
    Numbering may restart at 1 only below a mock, subject or role heading on the same page."""
    kept=[];prev=last
    for item in sorted(anchors,key=lambda a:(int(a[0]['rect'][0]>.46),a[0]['rect'][1])):
        number,qprefix,alone=item[1];right=item[0]['rect'][0]>.46
        restart=number==1 and any(y<item[0]['rect'][1] for y in resets)
        if prev and not qprefix and number!=prev+1 and not restart and (right or not alone or number<prev or number>prev+20):continue
        kept.append(item);prev=number
    return kept


def option_family(value, lines):
    """Printed option labels; two-column options read row-wise (A, C, B, D) still count as one A–D set."""
    family,matches,ambiguous=choose_options(value)
    if family:return family,ambiguous
    starts=[re.match(r'^\(([A-D1-4])\)|^([A-D])[.)]\s',x.strip()) for x in lines]
    labels={m[1] or m[2] for m in starts if m}
    for candidate,other in (('ABCD','1234'),('1234','ABCD')):
        if set(candidate)<=labels and not set(other)<=labels:return candidate,False
    return '',ambiguous


def page_map(classification, regions, issues):
    return PageMap(classification=classification,regions=regions,issues=list(dict.fromkeys(issues))[:30])


def continued_solution(open_s, rect, value):
    """A worked solution running on from the previous page, before the next 'Question N' heading."""
    return Region(role='solution',mock=open_s['mock'],subject=open_s['subject'],section=open_s['subject'],number=open_s['number'],
        rect=rect,text=value[:30000],continuation=True,checked=True)


def chapter_headings(lines, context):
    """Chapter-wise books: printed chapter headings. Under the owner's or the PDF's own chapter plan, only a printed
    key/solution heading of the current chapter is used, so a key table and its solutions can share a page."""
    if not context.get('chapters'):
        return [],set()
    marks,used=chapter_marks(lines,context.get('chapter_info') or {},band)
    if context.get('plan'):
        # A chapter that is itself called 'Solutions' prints 'CH 09 / Solutions' on every page: that is its name, not the start of worked solutions.
        own=re.sub(r'^\d+\s*','',norm(((context.get('chapter_info') or {}).get(context.get('mock')) or {}).get('title')))
        return [m for m in marks if m['role'] and m['label']==context.get('mock') and not (m.get('bare') and own in ('solution','solutions'))],set()
    return marks,used


def read_keys(lines, body, pairs, context):
    """One checked key region per printed table cell pair, assigned to the nearest mock title above it."""
    if context.get('chapters'):
        marks,_=chapter_headings(lines,context)
        titles=sorted((m['y'],m['label']) for m in marks)
        for m in marks:apply(context,'chapter',(m['label'],m['record']))
    else:
        titles=sorted((x['rect'][1],'Mock '+str(int(m[1]))) for x in lines for m in [mock_title(x['text'].strip())] if m)
    regions=[]
    for number,answer,rect in pairs:
        label=next((t[1] for t in reversed(titles) if t[0]<=rect[1]),context.get('mock',''))
        regions.append(Region(role='key',mock=label,number=number,rect=pad(rect),text=f'{number} {answer}',answer=answer,
            response_type='integer' if answer[-1].isdigit() else 'mcq',checked=bool(label)))
    issues=[] if all(r.mock for r in regions) else ['Answer key table has no mock title; map it to its mock.']
    if titles:context['mock']=titles[-1][1]
    context['role']='key';context.pop('open_q',None);context.pop('last',None)
    context['seen']=True
    return page_map('answer_key',regions,issues),context


def scan_headers(lines, text, context, issues):
    headers=[]; qprefixed=[]; others=[]
    chapters=context.get('chapters')
    starts=[round(x['rect'][0],2) for x in lines if x['rect'][0]<.3 and not band(x)]
    left=max(set(starts),key=starts.count) if starts else .3
    marks,used=chapter_headings(lines,context)
    # The bookmarks name the chapter: its title printed on a question page ('Solutions', 'Chemistry in Everyday Life') is not a heading.
    title=((context.get('chapter_info') or {}).get(context.get('mock')) or {}).get('title','') if context.get('plan') else ''
    title=re.sub(r'^\s*\d{1,3}[.)]?\s+','',title).strip().lower()
    for c in marks:
        headers+=[(c['y'],'mock',c['label']),(c['y'],'chapter',(c['label'],c['record']))]+([(c['y'],'role',c['role'])] if c['role'] else [])+[(y,'title',None) for y in c['rows'][1:]]
    for i,line in enumerate(lines):
        value=line['text'].strip();margin=band(line)
        if title and value.lower()==title and i not in used:continue
        crumb=None if chapters or i in used else crumbs(value)
        if crumb:
            # A running label names the page's mock, subject, section type or role wherever it is printed; it never splits a question.
            mock,subject,found,numeric=crumb
            if mock and mock!=context.get('mock'):headers.append((-1,'mock',mock))
            if found and (not margin or line['rect'][0]<.2 or line['rect'][2]>.85):headers.append((-1,'role','solution' if 'solution' in found[1].lower() else 'key'))
            if subject:headers.append((-1,'subject',subject))
            if numeric is not None:headers.append((-1,'numeric',numeric))
            continue
        m=None if chapters else mock_title(value)
        role=(ROLE.fullmatch(value) if chapters else role_of(value)) if value[:1].isupper() else None
        if m:
            headers.append((line['rect'][1],'mock','Mock '+str(int(m[1]))))
            starts_questions=bool(re.search(r'\b(?:instructions|duration|total questions|time\s*:)\b',text,re.I) or choose_options(text)[0])
            if context.get('role') in ('key','solution') and not starts_questions and not margin and context.get('mock')=='Mock '+str(int(m[1])):
                issues.append('Mock heading follows keys/solutions without question instructions: confirm the section type.')
        if role and i not in used and len(value)<140 and (not margin or line['rect'][0]<.2 or (not chapters and line['rect'][3]<=TOP and line['rect'][2]>.85)):
            # A running section label at the left margin (or right-aligned at the top) names the whole page; centred navigation links do not.
            headers.append((-1 if margin else line['rect'][1],'role','solution' if 'solution' in role[1].lower() else 'key'))
        if margin or i in used:continue
        subject=SUBJECT.match(value) if value[:1].isupper() and len(value.split())<=7 and not value.endswith(('.',',',';')) else None
        # In a chapter-wise book a subject heading names the chapter's subject; Exercise / Level / Part headings split its numbering.
        if subject and len(value)<90:headers.append((line['rect'][1],'seen_subject' if chapters else 'subject',subject[1].title().replace('Maths','Mathematics')))
        if chapters and exercise(value):headers.append((line['rect'][1],'subject',exercise(value)))
        section=SECTION.match(value)
        if section and len(value)<90:headers.append((line['rect'][1],'numeric',section[1].lower()=='b' or bool(NUMERIC.search(value))))
        elif NUMERIC_HEAD.match(value) and not ENTRY.match(value):headers.append((line['rect'][1],'numeric',True))
        passage=PASSAGE.match(value)
        if passage:headers.append((line['rect'][1],'shared',(int(passage[1]),int(passage[2] or passage[1]))))
        a=anchor_of(line)
        # Numbers hang at or left of the text margin; '5)' inside a formula sits to its right.
        if a and ((line['rect'][0]<.27 and line['rect'][0]<=left+.02) or .46<line['rect'][0]<.68):(qprefixed if a[1] else others).append((line,a))
    return sorted(headers,key=lambda h:h[0]),qprefixed or others  # explicit "Question N" headings outrank numbered steps


def apply(target, kind, value):
    if kind=='mock':
        if target.get('mock')!=value:
            target.update(mock=value,role='question',last={})
            if target.get('chapters'):target.update(subject='Questions',numeric=False)
    elif kind=='subject':target.update(subject=value,numeric=False)
    elif kind in ('role','numeric'):target[kind]=value
    elif kind=='chapter':
        label,record=value
        info={k:dict(v) for k,v in (target.get('chapter_info') or {}).items()};current=info.setdefault(label,{})
        for k,v in record.items():
            if v and not current.get(k):current[k]=v
        target['chapter_info']=info
    elif kind=='seen_subject':
        if target.get('mock'):apply(target,'chapter',(target['mock'],{'subject':value}))
        else:target['book_subjects']=sorted(set(target.get('book_subjects') or [])|{value})


def printed_keys(value, role):
    explicit={k.replace('\u2212','-').upper() for k in PRINTED.findall(value)}
    return explicit if explicit and role in ('key','solution') else {m[1].upper() for m in ANSWER_NEAR.finditer(value)}


def read_page(lines, previous, geometry=(), images=()):
    context=dict(previous); regions=[]; issues=[]
    # A tall page prints its first 'Question N' heading inside the top margin: that heading, and what is printed beside or under it, is the page's body and not a running header.
    high=[x['rect'][1] for x in lines if x['rect'][3]<=TOP+.02 and (anchor_of(x) or (0,False))[1]]
    for x in lines:
        if high and x['rect'][3]<=TOP+.03 and x['rect'][1]>=min(high)-.004:x['body']=True
    text='\n'.join(x['text'] for x in lines)
    if not lines:
        return PageMap(issues=['Scanned or empty page: approve AI reading or map the original page manually.']),context
    body=[x for x in lines if not band(x)];margin=[x for x in lines if band(x)]
    ceiling=max([x['rect'][3] for x in margin if x['rect'][3]<=TOP]+[0])+.002
    body_text='\n'.join(x['text'] for x in body)
    foot=min([x['rect'][1] for x in margin if x['rect'][1]>=BOTTOM]+[.97])-.004
    footer_text=' '.join(x['text'] for x in margin if x['rect'][1]>=BOTTOM)
    titles={m['label'] for m in chapter_headings(body,context)[0]} if context.get('chapters') else {int(m[1]) for x in lines for m in [mock_title(x['text'].strip())] if m}
    margin_anchor=any(anchor_of(x) for x in body if x['rect'][0]<.27)
    is_role=ROLE.fullmatch if context.get('chapters') else role_of
    if (re.search(r'^\s*(contents|index)\b',body_text,re.I|re.M) and not margin_anchor) or (len(titles)>=3 and not any(is_role(x['text'].strip()) for x in body)):
        return page_map('contents',[Region(role='ignore',rect=[.01,.01,.99,.99],text=text[:30000],checked=True)],[]),context
    if any(is_role(x['text'].strip()) and 'solution' not in x['text'].lower() for x in body) or (context.get('chapters') and any(c['role']=='key' for c in chapter_headings(body,context)[0])):
        # A key table and the start of the worked solutions may share a page: the table above, the solutions from their heading down.
        split=min([c['y'] for c in chapter_headings(body,context)[0] if c['role']=='solution']+[x['rect'][1] for x in body if is_role(x['text'].strip()) and 'solution' in x['text'].lower()]+[2])
        upper=[x for x in body if x['rect'][1]<split-.002]
        pairs=key_cells(upper,ruled=not context.get('chapters'))
        if pairs and split>1:return read_keys(lines,body,pairs,context)
        if pairs:
            keys,context=read_keys(margin+upper,upper,pairs,context)
            rest,context=read_page(margin+[x for x in body if x['rect'][1]>=split-.002],context,[g for g in geometry if g[1]>=split-.004],[b for b in images if b[1]>=split-.004])
            return page_map('mixed',keys.regions+rest.regions,keys.issues+rest.issues),context
    if context.get('plan') and context.get('role')=='key':
        # The book's own bookmarks say this page is an answer key: a ruled column of 'Q01 … A' rows is one even though 'Q01' looks like a
        # question number; otherwise a table of bare numbers is read as one only when nothing on the page starts a question.
        pairs=key_cells(body,5,ruled='only') or (key_cells(body,1) if not any(anchor_of(x) for x in body) else [])
        if pairs:return read_keys(lines,body,pairs,context)
    headers,anchors=scan_headers(lines,text,context,issues)
    page_role=next((v for y,k,v in headers if k=='role' and y<0),context.get('role'))
    if any(k=='mock' and v!=context.get('mock') for _,k,v in headers):page_role='question'
    if page_role=='solution' and context.get('solution_style')=='q':
        # Books that head every solution 'Question N' number their working steps 1., 2., … too.
        anchors=[a for a in anchors if a[1][1]]
    elif page_role=='solution':
        # '1. Answer (A)' heads each solution; the '1.', '2.' steps inside it are not new solutions.
        marked=[a for a in anchors if ANSWERED.match(a[0]['text'])]
        if marked:context['solution_style']='answer'
        if marked or context.get('solution_style')=='answer':anchors=marked
    if sum(x['rect'][0]<.45 and x['rect'][2]>.55 for x in body)>3:
        # Lines running across the gutter mean one column; a '5. …' fragment mid-row is not a second column.
        anchors=[a for a in anchors if a[0]['rect'][0]<=.46]
    resets=[h[0] for h in headers if h[1]=='subject' or (h[1]=='mock' and h[2]!=context.get('mock')) or (h[1]=='role' and h[2]!=context.get('role'))]
    anchors=in_sequence(anchors,(context.get('last') or {}).get(context.get('role','question'),0),resets)
    two=any(x[0]['rect'][0]>.46 for x in anchors) and any(x[0]['rect'][0]<.3 for x in anchors)
    if two:
        issues.append('Two-column layout: confirm column boundaries and continuation regions in the review desk.')
    if len({h[2] for h in headers if h[1]=='mock'})>1 and (two or not context.get('chapters')):
        issues.append('Multiple mock headings share this page; map their regions explicitly.')
    shared=[h for h in headers if h[1]=='shared']
    open_q=context.pop('open_q',None);open_s=context.pop('open_s',None)
    if not anchors and not shared:
        lead=context.get('single') and not context.get('seen') and not open_q and not re.search(r'\b(duration|instructions|marking)\b',text,re.I)
        if lead or (not context.get('mock') and not any(h[1]=='mock' for h in headers)):
            return page_map('cover',[Region(role='ignore',rect=[.01,.01,.99,.99],text=text[:30000],checked=True)],[]),context
        for _,kind,value in headers:apply(context,kind,value)
        if open_s and context.get('role')=='solution' and context.get('mock')==open_s['mock'] and body_text.strip():
            context['open_s']=open_s
            return page_map('solutions',[continued_solution(open_s,[.02,ceiling,.98,foot],body_text)],issues),context
        classification='instructions' if headers or re.search(r'\b(duration|instructions|marking)\b',text,re.I) else 'unresolved'
        if classification=='unresolved':issues.append('No reliable question or key anchors; classify or attach this continuation.')
        if open_q:issues.append(f'Q{open_q["number"]} (starts on the previous page): confirm response type, options and continuation.')
        regions=[Region(role='instructions' if classification=='instructions' else 'ignore',mock=context.get('mock',''),rect=[.01,.01,.99,.99],text=text[:30000],checked=classification=='instructions')]
        return page_map(classification,regions,issues),context
    first=min([a[0]['rect'][1] for a in anchors]+[h[0] for h in shared])
    for y,kind,value in headers:
        if y<=first+.006:apply(context,kind,value)
    boxes=[x['rect'] for x in body]+[g for g in geometry if ceiling<g[3] and g[1]<BOTTOM and g[3]-g[1]<.4]
    pictures=[list(b) for b in images]
    header_rows={round(h[0],3) for h in headers}
    header_rects=[x['rect'] for x in body if round(x['rect'][1],3) in header_rows]
    delimiters={id(x['rect']) for x in body if DELIMITER.fullmatch(x['text'].strip())}
    starts=sorted([(int(two and a[0]['rect'][0]>.46),a[0]['rect'][1],'anchor',a) for a in anchors]+[(0,h[0],'shared',h) for h in shared],key=lambda s:(s[0],s[1]))
    def column(col):
        x0,x1=(.02,.98) if not two else (.02,.49) if col==0 else (.5,.98)
        return [b for b in boxes if min(x1,b[2])-max(x0,b[0])>.002]
    def cut_for(col,y,kind,item):
        if kind!='anchor':return max(ceiling,y-.002)
        x0=item[0]['rect'][0]
        floor=max([ceiling]+[r[3]-.003 for r in header_rects if r[3]<=item[0]['rect'][1]+.002])
        top=row_top(item[0],[b for b in column(col) if b not in header_rects],delimiters)
        if open_q is None and not any(s[0]==col and s[1]<y for s in starts):
            # Only the page's first question may own an inline table header set just above its first line.
            top=min([top]+[x['rect'][1] for x in body if x['rect'][0]>x0+.3 and top-.006<x['rect'][3]<=top+.001 and x['rect'][3]-x['rect'][1]<.05 and not re.match(r'^\(?[A-D]\)',x['text'].strip())])
        # Tall rows touch: split the overlap between the previous row's descent and this row's raised glyphs.
        intruding=[b[3] for b in column(col) if b[3]-b[1]<.05 and b[1]<top-.004 and top<b[3]<=top+.012]
        return max(floor,min(item[0]['rect'][1]-.001,top+.003,(top+max(intruding))/2) if intruding else top-.002)
    cuts=[cut_for(*s) for s in starts]
    first=min(cuts)
    above=[x for x in body if x['rect'][1]<first]
    intro='\n'.join(x['text'] for x in above if round(x['rect'][1],3) not in header_rows)
    if above:
        rect=[.01,ceiling,.99,max(ceiling+.002,first-.001)]
        if intro.strip() and open_q and open_q.get('mock')==context.get('mock') and not INTRO_OK.search(intro):
            family,_=option_family(intro,intro.splitlines())
            regions.append(Region(role='question',mock=open_q['mock'],subject=open_q['subject'],section=open_q['subject'],number=open_q['number'],rect=rect,
                text=intro[:30000],option_labels=list(family),response_type='mcq' if family else 'unresolved',continuation=True,checked=bool(family)))
            if not family:issues.append(f'Q{open_q["number"]} (starts on the previous page): confirm response type, options and continuation.')
            open_q=None
        elif intro.strip() and open_s and context.get('role')=='solution' and open_s.get('mock')==context.get('mock'):
            regions.append(continued_solution(open_s,rect,intro))
        else:
            allowed=r'^(?:jee|bitsat|comedk|mock|practice|test|paper|time|duration|questions|total|correct|incorrect|wrong|unanswered|skipped|all\s+questions|instructions|physics|chemistry|math|solutions?|answers?|no\s+worked|page|english|logical|numerical|section)\b'
            chapter_intro=context.get('chapters') and any(h[1]=='mock' and h[0]<first for h in headers)
            if context.get('chapters'):allowed=allowed[:-3]+r'|\d{1,3}\s*[–\-]\s*\d{1,3})\b'
            # A group label ending '(Q16–Q30)' announces exactly the questions that follow; it is not a continuation.
            announced=re.search(r'\(\s*Q?\s*(\d{1,3})\s*[–\-]\s*Q?\s*\d{1,3}\s*\)\s*$',intro.strip(),re.I)
            announced=bool(announced and int(announced[1])==next((s[3][1][0] for s in starts if s[2]=='anchor'),None))
            if intro.strip() and not INTRO_OK.search(intro) and not chapter_intro and not announced and any(not re.search(allowed,line.strip(),re.I) for line in intro.splitlines() if len(line.strip())>3):
                issues.append('Leading content may continue a previous question or solution. Attach it explicitly instead of discarding it as instructions.')
            regions.append(Region(role='instructions',mock=context.get('mock',''),rect=rect,text='\n'.join(x['text'] for x in above)[:30000],checked=True))
    if open_q:issues.append(f'Q{open_q["number"]} (starts on the previous page): confirm response type, options and continuation.')
    last=dict(context.get('last') or {});running=context.get('mock');carry=None;solution_carry=None;base=dict(previous)
    for _,kind,value in headers:
        if kind=='role' and value and _<0:apply(base,kind,value)
    for i,(col,y,kind,item) in enumerate(starts):
        top=cuts[i]
        local=dict(base)
        for hy,hkind,value in headers:
            if hy<=y+.002:apply(local,hkind,value)
        if local.get('mock')!=running:last={};running=local.get('mock')
        end=next((cuts[j] for j in range(i+1,len(starts)) if starts[j][0]==col),foot)
        breaks=[h[0]-.002 for h in headers if y+.01<h[0]<end and h[1]!='numeric']
        if breaks:end=min(breaks)
        if end<=top:continue
        rect=[.02 if col==0 else .5,top,.49 if two and col==0 else .98,min(end,.999)]
        entry=[x for x in body if ENTRY.match(x['text'].strip()) and y<x['rect'][1]<end and rect[0]-.01<=x['rect'][0]<rect[2]]
        if entry:
            # The answer-entry box is not part of the question: the picture ends above it (above its ruled box when it has one).
            e=entry[0]['rect'];inside=[g[1] for g in geometry if g[0]<=e[0]+.002 and g[2]>=e[2]-.002 and y+.02<g[1]<=e[1]+.002 and g[3]>=e[3]-.002 and g[3]-g[1]<.2]
            end=max(top+.01,(max(inside) if inside else e[1])-.004);rect[3]=min(rect[3],end)
        group=[x for x in body if kind=='anchor' and y+.01<x['rect'][1]<end and rect[0]-.01<=x['rect'][0]<rect[2] and (m:=GROUP.search(x['text'].strip())) and int(m[1])==item[1][0]+1]
        if group:
            # A group label such as 'Two chapters (Q31–Q50)' announces the questions after this one: this question's picture ends above it (above its banner when it has one).
            g0=min(group,key=lambda x:x['rect'][1])['rect']
            row=[x['rect'] for x in body if abs((x['rect'][1]+x['rect'][3])-(g0[1]+g0[3]))<.012 and rect[0]-.01<=x['rect'][0]<rect[2]]
            label_top=min(r[1] for r in row);label_left=min(r[0] for r in row)
            banner=[g[1] for g in geometry if g[0]<=label_left+.002 and g[2]>=g0[2]-.002 and y+.02<g[1]<=label_top+.002 and g[3]>=g0[3]-.002 and g[3]-g[1]<.2]
            end=max(top+.01,min(banner+[label_top])-.004);rect[3]=min(rect[3],end)
        printed=[b for b in [x['rect'] for x in body]+[g for g in geometry if ceiling<g[3] and g[1]<BOTTOM] if top-.004<=b[1]<end and min(rect[2],b[2])-max(rect[0],b[0])>.002]
        if printed:rect[3]=min(rect[3],max(b[3] for b in printed)+.012)  # no blank page tail under the last line or figure
        value='\n'.join(x['text'] for x in body if rect[0]-.01<=x['rect'][0]<rect[2] and top<=x['rect'][1]<end)
        region_lines=[x['text'] for x in body if rect[0]-.01<=x['rect'][0]<rect[2] and top<=x['rect'][1]<end]
        if kind=='shared':
            low,high=item[2]
            # A subject heading printed between the passage and its question names the passage's section.
            following=[h for h in headers if h[1]=='subject' and y<h[0] and not any(s[2]=='anchor' and y<s[1]<h[0] for s in starts)]
            subject=following[0][2] if following else local.get('subject','')
            regions.append(Region(role='shared',mock=local.get('mock',''),subject=subject,section=subject,rect=rect,
                text=value[:30000],shared_for=list(range(low,min(high,low+30)+1)),checked=bool(local.get('mock') and subject)))
            continue
        line,(number,qprefix,_)=item
        for box in column(col):
            intersects=min(rect[2],box[2])-max(rect[0],box[0])>.002 and min(rect[3],box[3])-max(rect[1],box[1])>.004
            inside=rect[0]-.002<=box[0] and rect[1]-.004<=box[1] and box[2]<=rect[2]+.002 and box[3]<=rect[3]+.004
            # Text printed inside an image's box beyond this region means that part of the image is blank margin.
            blank=box in pictures and any(not (top<=x['rect'][1]<end) and min(box[2],x['rect'][2])-max(box[0],x['rect'][0])>.002 and min(box[3],x['rect'][3])-max(box[1],x['rect'][1])>.002 for x in lines)
            if intersects and not inside and not blank:
                issues.append(f'Q{number}: crop boundary crosses text or a diagram; adjust the region.')
                break
        role=local.get('role','question')
        family,ambiguous=option_family(value,region_lines)
        if role=='question' and local.get('numeric') and family and re.search(r'\(E\)|\bList[- ]?I\b',value):
            # A numerical-section match list labels its items (A)–(E); they are not answer options.
            family,ambiguous='',False
        keys=printed_keys(value,role)
        if role=='key':
            m=ANCHOR.match(line['text'].strip());tail=(m[3] if m else '').strip(); exact=re.fullmatch(r'[\[(]?([A-D]|[+\-]?\d{1,20})[\])]?',tail,re.I)
            if exact:keys.add(exact[1].upper())
        if len(keys)>1: issues.append(f'Conflicting printed keys near Q{number}.')
        if role=='question' and keys:issues.append(f'Answer visible near Q{number}; separate it from the question crop.')
        if not local.get('mock'):issues.append('Mock identity needs an explicit heading or owner mapping.')
        if not local.get('subject') and role=='question':issues.append('Subject/section identity needs confirmation.')
        consecutive=number in (1,last.get(role,0)+1);last[role]=number
        kind_of='mcq' if family else 'integer' if role=='question' and (entry or local.get('numeric') or NUMERIC.search(footer_text)) else 'unresolved'
        if role=='question' and kind_of=='unresolved':
            if not any(s[0]==col for s in starts[i+1:]) and end>=foot-.001:carry={'mock':local.get('mock',''),'subject':local.get('subject',''),'number':number}
            else:issues.append(f'Q{number}: confirm response type, options and continuation.')
        if role=='solution' and not qprefix and not consecutive:issues.append('Bare solution numbers may be numbered steps; confirm anchors.')
        if role=='solution' and qprefix:context['solution_style']='q'
        if role=='solution' and not any(s[0]==col for s in starts[i+1:]) and end>=foot-.001:solution_carry={'mock':local.get('mock',''),'subject':local.get('subject',''),'number':number}
        regions.append(Region(role=role,mock=local.get('mock',''),subject=local.get('subject',''),section=local.get('subject',''),
            number=number,rect=rect,text=value[:30000],answer=next(iter(keys)) if len(keys)==1 else '',
            option_labels=list(family),response_type=kind_of,checked=not two and not ambiguous and (qprefix or consecutive)))
    for y,kind,value in headers:apply(context,kind,value)
    context['last']=last;context['seen']=True
    if carry:context['open_q']=carry
    if solution_carry:context['open_s']=solution_carry
    roles={r.role for r in regions if r.role not in ('instructions','ignore','shared')}
    classification={'question':'questions','key':'answer_key','solution':'solutions'}.get(next(iter(roles)),'mixed') if len(roles)==1 else 'mixed'
    return page_map(classification,regions,issues),context


def infer_rules(text):
    def match(pattern):return re.search(pattern,text,re.I)
    duration=match(r'(?:duration|time(?:\s+allowed)?)\s*[:=]?\s*(\d+)\s*(minutes?|mins?|hours?|hrs?)')
    count=match(r'(?:total\s+(?:number\s+of\s+)?questions|questions)\s*[:=]\s*(\d+)') or match(r'\b(\d{1,3})\s+(?:main\s+)?questions\b')
    bonus=match(r'\b(\d{1,2})\s+(?:optional\s+)?bonus\s+questions\b')
    correct=match(r'(?:correct(?:\s+answer)?)\s*[:=]?\s*\+?(\d+(?:\.\d+)?)')
    wrong=match(r'(?:wrong|incorrect)(?:\s+answer)?\s*[:=]?\s*[-\u2212\u2013]?\s*(\d+(?:\.\d+)?)')
    skipped=match(r'(?:unanswered|skipped|not\s+attempted)\s*[:=]?\s*0\b')
    exam=next((x for x in ('JEE Main','BITSAT','COMEDK') if x.lower() in text.lower()),None)
    bitsat=bool(exam=='BITSAT' and bonus and int(bonus[1])==12)
    plain=re.sub(r'\boptional\s+bonus\b','bonus',text,flags=re.I) if bitsat else text
    compulsory=bool(match(r'all\s+(?:\d+\s+)?questions\s+(?:are\s+)?compulsory')) or bitsat or bool(skipped and not re.search(r'\b(optional|attempt\s+any)\b',plain,re.I))
    unsupported=bool(re.search(r'\b(optional|attempt\s+any|round(?:ing|ed)|decimal|multiple\s+correct)\b',plain,re.I)) or (bool(re.search(r'\bbonus\b',plain,re.I)) and not bitsat)
    correct_values=set(re.findall(r'(?<!in)\bcorrect(?:\s+answer)?\s*[:=]?\s*\+?(\d+(?:\.\d+)?)',text,re.I))
    wrong_values=set(re.findall(r'\b(?:wrong|incorrect)(?:\s+answer)?\s*[:=]?\s*[-\u2212\u2013]?\s*(\d+(?:\.\d+)?)',text,re.I))
    if len(correct_values)>1 or len(wrong_values)>1:return {}
    if not all((duration,count,correct,wrong,skipped,exam,compulsory)) or unsupported:return {}
    extra=12 if bitsat else 0
    return {'exam':exam,'minutes':int(duration[1])*(60 if duration[2].lower().startswith('h') else 1),'expected_questions':int(count[1])+extra,
        'correct':float(correct[1]),'wrong':-abs(float(wrong[1])),'skipped':0,'mechanic':'bitsat_bonus' if bitsat else 'all_compulsory','bonus_count':extra,
        'first_number':1,'numbering':'continuous','solution_policy':'key_only' if match(r'no\s+worked\s+solutions|answer\s+key\s+only') else 'original_expected',
        'key_only':[],'unsupported':'','note':'Explicit printed instructions; no examination preset inferred.'}
