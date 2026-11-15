import copy, json, re
from starlette.concurrency import run_in_threadpool
from .db import db, sets, files, now, audit
from .canonical import database_now
from .book_models import BookMock, MockRules
from .book_store import identity, normalized, save_mock, pages_for, mocks_for, fence, renew, digest, principal
from .book_reader import infer_rules
from .book_pdf import inspect_many
from .content import valid_rules, question_issues, publish_validated
from .chapter_reader import book_subjects, match_subject, syllabus_subject, resolve_subject, bookmark_title
from tejas_storage import put_object


def overlap(a,b):
    return min(a[2],b[2])-max(a[0],b[0])>.001 and min(a[3],b[3])-max(a[1],b[1])>.001


def question_identity(r):return (normalized(r.subject),normalized(r.section or r.subject),r.number)


async def chapter_context(book, pages):
    """What the pages say about each chapter (number, title, subject), plus the book's single subject if it names one."""
    info,found={},set()
    for p in pages:
        for label,record in (p.context.get('chapter_info') or {}).items():
            current=info.setdefault(normalized(label),{})
            for k,v in record.items():
                if v and not current.get(k):current[k]=v
        found|=set(p.context.get('book_subjects') or [])
    pl=book.payload;dest=pl.get('destination') or {}
    allowed=(await db.tejas_catalog_exams.find_one({'_id':dest.get('exam_slug')},{'_id':0,'subjects':1}) or {}).get('subjects') or []
    named={s for s in found|book_subjects(pl.get('title',''))|book_subjects(pl.get('filename','')) if match_subject(s,allowed)}
    return {'info':info,'allowed':allowed,'book':next(iter(named)) if len(named)==1 else '','marks':pl.get('bookmarks') or []}


def chapter_record(book, mock, label, relevant, ctx, order):
    record=ctx['info'].get(label,{});override=(book.payload.get('chapter_overrides') or {}).get(label,{})
    pages=sorted({p.number for p,r in relevant if r.role=='question'}) or sorted({p.number for p,_ in relevant})
    title=override.get('title') or record.get('title') or bookmark_title(ctx['marks'],pages[0] if pages else 0) or mock.label
    marked=book.payload.get('plan_source')=='owner'
    subject,source=resolve_subject([(override.get('subject'),'you'),(record.get('subject') if marked else '','you'),(book.payload.get('subject'),'upload'),(record.get('subject'),'pdf'),(ctx['book'],'book'),(syllabus_subject(title),'name')],ctx['allowed'])
    return {'number':record.get('number') or order,'title':title[:120],'subject':subject,'subject_from':source,'start_page':pages[0] if pages else None}


async def rebuild(book, token):
    pages=await pages_for(book); known={normalized(m.label):m for m in await mocks_for(book)}
    chapters=await chapter_context(book,pages) if book.payload.get('chapters') else None
    labels=list(dict.fromkeys(normalized(r.mock) for p in pages for r in p.regions if r.mock and r.role not in ('ignore','instructions')))
    by_label={}
    for p in pages:
        for r in p.regions:
            if r.mock and r.role!='ignore':by_label.setdefault(normalized(r.mock),[]).append((p,r))
    unknown=[p.number for p in pages if p.classification=='unresolved' or (p.issues and not any(r.mock for r in p.regions))]
    spans={}
    for p in pages:
        for r in p.regions:
            if r.mock and r.role!='ignore':
                key=normalized(r.mock);bounds=spans.setdefault(key,[p.number,p.number]);bounds[1]=p.number
    affected={}
    for number in unknown:
        containing={label for label,(first,last) in spans.items() if first<=number<=last}
        if not containing:
            before=[p for p in pages if p.number<number and any(r.mock for r in p.regions)]
            after=[p for p in pages if p.number>number and any(r.mock for r in p.regions)]
            neighbours=(before[-1:] if before else [])+(after[:1] if after else [])
            containing={normalized(r.mock) for p in neighbours for r in p.regions if r.mock}
        affected[number]=containing
    for order,label in enumerate(labels,1):
        relevant=by_label[label]
        mock=known.get(label) or BookMock(id=identity(book.id,label),book_id=book.id,label=relevant[0][1].mock,order=order)
        if mock.published_generation==mock.generation:continue
        mock.order=order;issues=[];question_groups={};key_groups={};solution_groups={}
        local_unknown=[number for number,affected_labels in affected.items() if label in affected_labels]
        if local_unknown:issues.append('Unmapped pages in or beside this mock’s source ranges need review: '+', '.join(map(str,local_unknown[:30])))
        printed=[]
        for p,r in relevant:
            if p.issues:issues.extend(f'Page {p.number}: {x}' for x in p.issues)
            if r.role=='instructions':continue
            if not r.checked:issues.append(f'Page {p.number}, Q{r.number}: source region needs review.')
            if r.role in ('question','key','solution') and (not r.number or (r.role=='question' and not r.subject)):issues.append(f'Page {p.number}: subject and printed question number are required.')
            if not r.complete:issues.append(f'Page {p.number}, Q{r.number}: unresolved continuation.')
            if r.role=='shared':
                if not r.shared_for:issues.append(f'Page {p.number}: shared passage must name its printed questions.')
                if r.answer or re.search(r'(?im)^\s*(?:answer|ans\.|solution|correct option)\s*[:=]',r.text) or any(other.role in ('key','solution') and overlap(r.rect,other.rect) for other in p.regions):
                    issues.append(f'Page {p.number}: shared passage exposes a key or solution.')
                continue
            if r.role!='question':
                printed.append((p,r));continue
            question_groups.setdefault(question_identity(r),[]).append((p,r))
            if r.role=='question':
                for other in p.regions:
                    if other is not r and other.role in ('key','solution','question') and overlap(r.rect,other.rect):
                        issues.append(f'Page {p.number}, Q{r.number}: question overlaps another question, key or solution.')
                # Printed keys sit at the start of a line; 'oxalate solution: white ppt' is chemistry, not a leaked answer.
                if r.answer or re.search(r'(?im)^\s*(?:answer|ans\.|solution|correct option)\s*[:=]',r.text):
                    issues.append(f'Page {p.number}, Q{r.number}: answer or solution visible in question region.')
        by_number={}
        for key in question_groups:by_number.setdefault(key[2],[]).append(key)
        for p,r in printed:
            # Keys and solutions printed by question number alone bind to the one question carrying that number.
            ident=question_identity(r)
            if ident not in question_groups and len(by_number.get(r.number,[]))==1:ident=by_number[r.number][0]
            (key_groups if r.role=='key' else solution_groups).setdefault(ident,[]).append((p,r))
        instructions=[(p,r) for p,r in relevant if r.role=='instructions']
        # A book that itself promises worked solutions never drops them silently; the owner decides per question in Fix.
        promised=bool(re.search(r'\b(?:worked|detailed)\s+solutions?\s+(?:follow|provided|included|for\s+(?:all|every))','\n'.join(r.text for _,r in instructions),re.I))
        if not mock.rules:
            inferred=infer_rules('\n'.join(r.text for _,r in instructions))
            if inferred:
                inferred['source_pages']=sorted({p.number for p,_ in instructions})[:30]
                if not solution_groups and any(re.search(r'\bquestions\s+only\b',p.text,re.I) for p,_ in relevant):inferred['solution_policy']='key_only'
                mock.rules=MockRules.model_validate(inferred).model_dump()
            elif question_groups and (book.payload.get('destination') or {}).get('defaults'):
                # Nothing printed: the mock type's own time and marks apply, as the owner set them.
                d=book.payload['destination']['defaults'];nums=[k[2] for k in question_groups]
                mock.rules=MockRules.model_validate({'exam':'Custom','minutes':d['minutes'],'expected_questions':len(question_groups),'correct':d['correct'],'wrong':d['wrong'],
                    'mechanic':'all_compulsory','numbering':'per_section' if len(set(nums))<len(nums) else 'continuous','first_number':max(1,min(nums)),
                    'solution_policy':'mixed','source_pages':[relevant[0][0].number],'note':'Default time and marks of this mock type; the PDF prints none.'}).model_dump()
        if mock.rules and mock.rules.get('note','').startswith('Default time and marks') and question_groups:
            nums=[k[2] for k in question_groups]
            mock.rules.update(expected_questions=len(nums),numbering='per_section' if len(set(nums))<len(nums) else 'continuous',first_number=max(1,min(nums)))
        if not mock.rules:issues.append('Confirm printed examination rules, count, duration, marking and solution coverage.')
        if mock.rules and book.payload.get('destination'):
            from .structure import rule_exam
            mock.rules['exam']=rule_exam(book.payload['destination'])
        rules=mock.rules
        if rules:
            if rules.get('unsupported') or rules['mechanic']=='unsupported':issues.append('Printed test mechanics are unsupported; this mock cannot publish.')
            if rules['mechanic']=='bitsat_bonus':
                if rules['exam']!='BITSAT' or rules['bonus_count']!=12 or rules['expected_questions']<=12:issues.append('Only the existing 12-question BITSAT bonus mechanic is supported.')
            elif rules['bonus_count']:issues.append('Bonus questions require the supported BITSAT bonus mechanic.')
            raw_instructions='\n'.join(r.text for _,r in instructions)
            if re.search(r'\b(?:worked|detailed)\s+solutions?\s+(?:follow|provided|included|for\s+(?:all|every))',raw_instructions,re.I) and rules.get('solution_policy')!='original_expected':
                issues.append('Printed instructions promise original worked solutions. Failed capture cannot be relabelled key-only.')
            declared_counts={int(n) for n in re.findall(r'(?:total\s+(?:number\s+of\s+)?questions|questions)\s*[:=]\s*(\d+)',raw_instructions,re.I)}
            if declared_counts and declared_counts!={rules['expected_questions']}:
                issues.append('Printed question count conflicts with the proposed count; a missing source question cannot be waived.')
            section_ids=[(normalized(s['subject']),normalized(s['section'])) for s in rules.get('section_scoring',[])]
            if len(section_ids)!=len(set(section_ids)) or any(key not in {k[:2] for k in question_groups} for key in section_ids):
                issues.append('Section marking has duplicate or unmapped section identities.')
            checked_text=re.sub(r'\boptional\s+bonus\b','bonus',raw_instructions,flags=re.I) if rules['mechanic']=='bitsat_bonus' else raw_instructions
            if chapters is not None:checked_text=re.sub(r'\boptional\s+(?:enrichment\s+)?(?:practice|reading|exercise)\b','practice',checked_text,flags=re.I)
            if re.search(r'\b(optional|attempt\s+any|round(?:ed|ing)|decimal|multiple\s+correct)\b',checked_text,re.I):
                issues.append('Printed optional/rounding/multiple-answer instructions cannot be converted to attempt-all or exact integers.')
            if len(question_groups)!=rules['expected_questions']:issues.append(f'Printed count {rules["expected_questions"]}; detected {len(question_groups)} distinct questions.')
            groups={}
            for key in question_groups:groups.setdefault(key[:2] if rules['numbering']=='per_section' else ('all',),[]).append(key[2])
            for nums in groups.values():
                if sorted(nums)!=list(range(rules['first_number'],rules['first_number']+len(nums))):issues.append('Unexplained missing or duplicate printed question numbers.')
        for p,r in relevant:
            if r.role=='shared' and any((normalized(r.subject),normalized(r.section or r.subject),n) not in question_groups for n in r.shared_for):
                issues.append(f'Page {p.number}: shared passage references a missing question.')
        questions=[]
        for position,(key,entries) in enumerate(question_groups.items(),1):
            first=entries[0][1];keys=key_groups.get(key,[]);solutions=solution_groups.get(key,[])
            if sum(not r.continuation for _,r in entries)!=1:issues.append(f'{first.subject} Q{first.number}: duplicate question or missing starting region.')
            if solutions and sum(not r.continuation for _,r in solutions)!=1:issues.append(f'{first.subject} Q{first.number}: ambiguous worked-solution start/continuations.')
            answers={r.answer.strip() for _,r in keys+solutions if r.answer.strip()}
            answer=next(iter(answers)) if len(answers)==1 else ''
            if not answer:issues.append(f'{first.subject} Q{first.number}: missing or conflicting supplied key.')
            labels_for_options=list(dict.fromkeys(x for _,r in entries for x in r.option_labels))
            kind=first.response_type if first.response_type!='unresolved' or len(labels_for_options)<2 else 'mcq'
            if kind=='unresolved':issues.append(f'{first.subject} Q{first.number}: response type is unresolved.')
            if kind=='mcq' and (len(labels_for_options)<2 or answer not in labels_for_options):issues.append(f'{first.subject} Q{first.number}: incomplete options or key does not match printed labels.')
            if kind=='integer' and not re.fullmatch(r'[+-]?\d{1,20}',answer):issues.append(f'{first.subject} Q{first.number}: unsupported exact-integer key.')
            coverage_key=f'{first.subject}|{first.section or first.subject}|{first.number}'
            source_expects=coverage_key in mock.original_solution_identities or bool(solutions)
            if solutions and coverage_key not in mock.original_solution_identities:mock.original_solution_identities.append(coverage_key)
            # An answer key is enough; a worked solution is optional unless this book printed one for the question.
            no_solution=not source_expects and ((bool(keys) and not promised and not solution_groups) or rules.get('solution_policy')=='key_only' or (rules.get('solution_policy')=='mixed' and coverage_key in rules.get('key_only',[])))
            if not solutions and not no_solution:issues.append(f'{first.subject} Q{first.number}: original solution expected but not captured; attach its regions.')
            if not solutions and not keys:issues.append(f'{first.subject} Q{first.number}: original key region required.')
            shared=[(p,r) for p,r in relevant if r.role=='shared' and normalized(r.subject)==key[0] and normalized(r.section or r.subject)==key[1] and key[2] in r.shared_for]
            qid=identity(mock.id,mock.generation,*key)
            questions.append({'id':qid,'number':position,'original_number':first.number,'subject':first.subject,'section':first.section or first.subject,
                'type':kind,'answer':answer,'options':{x:'Original option '+x for x in labels_for_options},
                'text':'\n'.join(r.text for _,r in entries) or f'Original question {first.number}; image transcription unavailable.',
                'solution_kind':'supplied_worked' if solutions else 'answer_key_only',
                'solution':'Original book worked solution.' if solutions else f'Supplied answer key: {answer}. This book does not contain a worked solution.',
                'source_regions':{'question':[{'page':p.number,'rect':r.rect} for p,r in shared+entries],
                                  'solution':[{'page':p.number,'rect':r.rect} for p,r in solutions or keys],
                                  'key':[{'page':p.number,'rect':r.rect,'printed_answer':r.answer} for p,r in keys+solutions if r.answer]},
                'coverage_key':coverage_key})
        for orphan in (set(solution_groups)|set(key_groups))-set(question_groups):issues.append('Key/solution has no matching question: '+str(orphan))
        # Holds placed at publication time must survive the next rebuild; only an owner action clears them.
        if mock.missed_release and not mock.release_override:issues.append('Missed scheduled release. Choose a new release decision; it will not launch late automatically.')
        if mock.publish_hold:issues.append(mock.publish_hold)
        if chapters is not None:
            mock.chapter=chapter_record(book,mock,label,relevant,chapters,order)
            if not mock.chapter['subject']:issues.append('Choose the subject for this chapter.')
        mock.pages={role:sorted({p.number for p,r in relevant if r.role==role}) for role in ('question','key','solution','instructions')}
        mock.questions=questions;mock.issues=list(dict.fromkeys(issues))[:500]
        if not questions:mock.issues.append('No complete questions found.')
        mock.state='held' if mock.issues else 'ready';mock.revision+=1
        if mock.state=='held':mock.publish_requested=False
        if book.payload.get('release_at') and await database_now()>=book.payload['release_at'] and mock.state=='held':mock.missed_release=True
        await fence(book,token);await save_mock(mock)
    for label,mock in known.items():
        if label not in labels and mock.published_generation!=mock.generation:
            mock.state='held';mock.questions=[];mock.issues=['All mapped regions were removed. Restore the mock boundaries.'];await save_mock(mock)


async def crop_ref(book,mock,crop,region,role):
    if crop.get('error'):raise ValueError(f"Page {region['page']}: {crop['error']}")
    png=crop['image_bytes'];fid=identity(book.id,digest(png),role)
    if not await files.find_one({'id':fid},{'_id':1}):
        path=await run_in_threadpool(put_object,f'jeelive/books/{book.id}/crops/{fid}.png',png,'image/png')
        await files.update_one({'id':fid},{'$setOnInsert':{'id':fid,'set_id':mock.set_id or identity(mock.id,mock.generation),
            'path':path,'kind':'rendered_png','sha256':digest(png),'source_sha256':book.payload['sha256'],
            'original_page':region['page'],'original_rect':region['rect'],'book_import_id':book.id,'created_at':now()}},upsert=True)
    return {'file_id':fid,'page':region['page'],'rect':region['rect'],'prerendered':True}


async def source_questions(book, mock, raw, guard=None, strict=True):
    """The mock's questions with original page crops, exactly as students receive them. Not strict: incomplete questions are left out and listed."""
    rules=mock.rules;chapter=mock.chapter or {}
    wanted=[(q['id'],role,region) for q in mock.questions for role in ('question','solution') for region in q['source_regions'][role]]
    rendered=await run_in_threadpool(inspect_many,raw,[{'action':'crop','page':r['page'],'rect':r['rect']} for _,_,r in wanted],10)
    crops={}
    for (qid,role,_),crop in zip(wanted,rendered):crops.setdefault((qid,role),[]).append(crop)
    if guard:await guard('renew')
    questions,left=[],[]
    for original_q in mock.questions:
        q=copy.deepcopy(original_q);source=q.pop('source_regions');q.pop('coverage_key',None)
        q.update(render_mode='source',solution_number=q['number'],approved=True,issues=[],q_refs=[],s_refs=[],
            accessible_text=q['text'],solution_accessible_text=q['solution'],review_note='Source-mapping checks passed; supplied key preserved, not independently academically certified.',
            source_evidence={'book_sha256':book.payload['sha256'],'edition':book.payload.get('edition',''),'mock':mock.label,'regions':source},
            source_warning='Original page images preserve notation. A fully accessible transcription is not available.')
        for section in rules.get('section_scoring',[]):
            if normalized(section['subject'])==normalized(q['subject']) and normalized(section['section'])==normalized(q['section']):
                q['scoring']={k:section[k] for k in ('correct','wrong','skipped')}
        if rules['mechanic']=='bitsat_bonus':q['bonus']=q['number']>rules['expected_questions']-rules['bonus_count']
        if chapter:
            # A chapter test carries its chapter's subject; Exercise / Level headings stay as its sections.
            subject=chapter.get('subject') or 'General'
            q['section']=subject if normalized(q['section']) in ('questions',normalized(q['subject'])) else q['section']
            q['subject']=subject
        try:
            for role,key in (('question','q_refs'),('solution','s_refs')):
                for region,crop in zip(source[role],crops.get((q['id'],role),[])):
                    if guard:await guard('fence')
                    q[key].append(await crop_ref(book,mock,crop,region,role))
            errors=question_issues(q,rules['exam'])
        except ValueError as exc:
            if strict:raise
            errors=[str(exc)]
        if errors:
            if strict:raise ValueError('; '.join(errors))
            left.append({'number':original_q['original_number'],'subject':original_q['subject'],'reason':errors[0]});continue
        questions.append(q)
    if len(json.dumps(questions).encode())>5*1024*1024:raise ValueError('This mock exceeds the safe content budget.')
    return questions,left


def base_set(book, mock, questions, dest, suffix=''):
    """The test record students get; publishing adds its id, timing and place."""
    rules=mock.rules;chapter=mock.chapter or {}
    title=chapter.get('title') or mock.label if chapter else mock.label if dest else book.payload['title']+' · '+mock.label
    data={'book_series_title':book.payload['title'],'mock_number':mock.order,'title':title+suffix,
        'exam':dest['exam_key'] if dest else rules['exam'],'test_kind':'mock','full_length':True,'profile_mode':'practice','rules':valid_rules({'minutes':rules['minutes'],'correct':rules['correct'],'wrong':rules['wrong'],'skipped':0}),
        'questions':questions,'file_ids':sorted({r['file_id'] for q in questions for k in ('q_refs','s_refs') for r in q[k]}),
        'status':'draft','version':0,'revision':1,'source':'Owner-uploaded '+book.payload['filename'],'attribution':'Original book source; owner-confirmed content-use rights.',
        'rights_upload':True,'rights_publish':True,'rights_report':True,'audience':'all','allowed_emails':[],'allowed_phones':[],'expires':'','created_at':now(),'created_by':book.owner_id}
    if chapter:
        kinds={q['solution_kind'] for q in questions}
        data.update(test_kind='chapter',full_length=False,chapter_subject=chapter.get('subject') or 'General',chapter_number=chapter.get('number') or mock.order,chapter_title=chapter.get('title') or mock.label)
        if len(kinds)==1:data['solution_kind']=kinds.pop()
    if rules['mechanic']=='bitsat_bonus':data['rules']['bonus_rule']='answer_all_main_then_lock'
    return data


async def publish_ready(book,token,raw,only_mid=None):
    if book.paused:return
    dest=book.payload.get('destination')
    series=bool(dest and dest.get('series'))
    for mock in await mocks_for(book):
        if only_mid and mock.id!=only_mid:continue
        if not (book.payload.get('auto_publish') or mock.publish_requested):continue
        if mock.state!='ready' or mock.issues or mock.published_generation==mock.generation:continue
        if series and not mock.series_date:continue
        if book.payload.get('release_at') and await database_now()>=book.payload['release_at'] and not mock.release_override:
            mock.missed_release=True
        if mock.missed_release and not mock.release_override:
            mock.state='held';mock.issues=['Missed scheduled release. Choose a new release decision; it will not launch late automatically.'];await save_mock(mock);continue
        await renew(book,token)
        sid=identity(mock.id,mock.generation);existing=await sets.find_one({'id':sid})
        if existing and existing.get('status')=='published':
            mock.set_id=sid;mock.published_generation=mock.generation;mock.state='published';await save_mock(mock);continue
        if series:
            from .live_series import window as day_window
            from .series_admin import series_cfg
            cfg=await series_cfg(dest.get('series_id'))
            opens=day_window(mock.series_date,cfg)['opens_at']
            if await database_now()>=opens or await sets.find_one({'series_id':cfg['id'],'series_date':mock.series_date,'id':{'$ne':sid}},{'_id':1}):
                # Its day opened or was taken before the paper was built: it waits, unassigned, for a new day.
                mock.series_date=None;mock.publish_requested=False;mock.release_at=None;await save_mock(mock);continue
        rules=mock.rules
        async def guard(kind):
            await (renew(book,token) if kind=='renew' else fence(book,token))
        questions,_=await source_questions(book,mock,raw,guard)
        stamp=await database_now();start=stamp if mock.release_override else mock.release_at or book.payload.get('release_at') or stamp
        suffix=f' · v{mock.generation}' if mock.generation>1 else ''
        data={'id':sid,'book_import_id':book.id,**base_set(book,mock,questions,dest,suffix),'live_enabled':True,'start_at':start,'competition':book.payload.get('competitive',False) or mock.live_exam}
        if series:
            w=day_window(mock.series_date,cfg);start=w['opens_at']
            data.update(series_id=cfg['id'],series_date=mock.series_date,series_window=w,series_import=True,start_at=start,end_at=w['closes_at'],competition=False)
            if cfg.get('pattern'):data['series_pattern']={**cfg['pattern'],'count':len(questions)}
        elif dest:
            from .structure import next_order
            if 'catalog_base' not in book.payload:book.payload['catalog_base']=(dest.get('replace_order') or await next_order(dest['section_id']))-1
            data.update(catalog_section_id=dest['section_id'],catalog_order=book.payload['catalog_base']+mock.order)
            if dest.get('pyq'):data.update(test_kind='pyq',master_pyq=True,pyq_year=dest['year'],pyq_date='',pyq_shift=0)
        if data['competition']:
            if mock.release_override:raise ValueError('An expired competitive window needs a new edition and future schedule.')
            from .live_window import window as live_window
            data['last_start_at'],data['end_at']=live_window(start,rules['minutes'],book.payload.get('closes_at') if book.payload.get('competitive') else None)
        await fence(book,token)
        await sets.update_one({'id':sid},{'$setOnInsert':data},upsert=True)
        await publish_validated(sid,{'confirm':True},await principal(book))
        if mock.set_id and mock.set_id!=sid:
            await sets.update_one({'id':mock.set_id,'book_import_id':book.id},{'$set':{'status':'withdrawn','live_enabled':False}})
            if mock.set_id not in mock.history:mock.history.append(mock.set_id)
        mock.set_id=sid;mock.published_generation=mock.generation;mock.publish_requested=False;mock.state='scheduled' if start>stamp else 'published';await save_mock(mock)
        if dest and dest.get('replaces') and not book.payload.get('replaced_at'):
            from .structure import apply_replacement
            book.payload['replaced_at']=now()
            await db.tejas_books.update_one({'_id':book.id},{'$set':{'payload.replaced_at':book.payload['replaced_at']}})
            await apply_replacement(dest,book.owner_id,book.payload['title'])
        book.payload.setdefault('metrics',{}).setdefault('first_ready_seconds',max(0,now()-book.created_at))
        await audit(book.owner_id,'Book mock published',sid,'Original keys and source evidence retained; previous attempts unchanged.')
