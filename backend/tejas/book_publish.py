import copy, json, re
from starlette.concurrency import run_in_threadpool
from .db import sets, files, now, audit
from .canonical import database_now
from .book_models import BookMock, MockRules
from .book_store import identity, normalized, save_mock, pages_for, mocks_for, fence, renew, digest, principal
from .book_reader import infer_rules
from .book_pdf import inspect_many
from .content import valid_rules, question_issues, publish_validated
from tejas_storage import put_object


def overlap(a,b):
    return min(a[2],b[2])-max(a[0],b[0])>.001 and min(a[3],b[3])-max(a[1],b[1])>.001


def question_identity(r):return (normalized(r.subject),normalized(r.section or r.subject),r.number)


async def rebuild(book, token):
    pages=await pages_for(book); known={normalized(m.label):m for m in await mocks_for(book)}
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
        if not mock.rules:
            inferred=infer_rules('\n'.join(r.text for _,r in instructions))
            if inferred:
                inferred['source_pages']=sorted({p.number for p,_ in instructions})[:30]
                if not solution_groups and any(re.search(r'\bquestions\s+only\b',p.text,re.I) for p,_ in relevant):inferred['solution_policy']='key_only'
                mock.rules=MockRules.model_validate(inferred).model_dump()
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
            no_solution=not source_expects and (rules.get('solution_policy')=='key_only' or (rules.get('solution_policy')=='mixed' and coverage_key in rules.get('key_only',[])))
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
    path=await run_in_threadpool(put_object,f'jeelive/books/{book.id}/crops/{fid}.png',png,'image/png')
    await files.update_one({'id':fid},{'$setOnInsert':{'id':fid,'set_id':mock.set_id or identity(mock.id,mock.generation),
        'path':path,'kind':'rendered_png','sha256':digest(png),'source_sha256':book.payload['sha256'],
        'original_page':region['page'],'original_rect':region['rect'],'book_import_id':book.id,'created_at':now()}},upsert=True)
    return {'file_id':fid,'page':region['page'],'rect':region['rect'],'prerendered':True}


async def publish_ready(book,token,raw,only_mid=None):
    if book.paused:return
    dest=book.payload.get('destination')
    for mock in await mocks_for(book):
        if only_mid and mock.id!=only_mid:continue
        if not (book.payload.get('auto_publish') or mock.publish_requested):continue
        if mock.state!='ready' or mock.issues or mock.published_generation==mock.generation:continue
        if book.payload.get('release_at') and await database_now()>=book.payload['release_at'] and not mock.release_override:
            mock.missed_release=True
        if mock.missed_release and not mock.release_override:
            mock.state='held';mock.issues=['Missed scheduled release. Choose a new release decision; it will not launch late automatically.'];await save_mock(mock);continue
        await renew(book,token)
        sid=identity(mock.id,mock.generation);existing=await sets.find_one({'id':sid})
        if existing and existing.get('status')=='published':
            mock.set_id=sid;mock.published_generation=mock.generation;mock.state='published';await save_mock(mock);continue
        questions=[];rules=mock.rules
        wanted=[(q['id'],role,region) for q in mock.questions for role in ('question','solution') for region in q['source_regions'][role]]
        rendered=await run_in_threadpool(inspect_many,raw,[{'action':'crop','page':r['page'],'rect':r['rect']} for _,_,r in wanted],10)
        crops={}
        for (qid,role,_),crop in zip(wanted,rendered):crops.setdefault((qid,role),[]).append(crop)
        await renew(book,token)
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
            for role,key in (('question','q_refs'),('solution','s_refs')):
                for region,crop in zip(source[role],crops.get((q['id'],role),[])):
                    await fence(book,token)
                    q[key].append(await crop_ref(book,mock,crop,region,role))
            errors=question_issues(q,rules['exam'])
            if errors:raise ValueError('; '.join(errors))
            questions.append(q)
        if len(json.dumps(questions).encode())>5*1024*1024:raise ValueError('This mock exceeds the safe content budget.')
        stamp=await database_now();start=stamp if mock.release_override else mock.release_at or book.payload.get('release_at') or stamp
        suffix=f' · v{mock.generation}' if mock.generation>1 else ''
        data={'id':sid,'book_import_id':book.id,'book_series_title':book.payload['title'],'mock_number':mock.order,
            'title':(mock.label if dest else book.payload['title']+' · '+mock.label)+suffix,
            'exam':dest['exam_key'] if dest else rules['exam'],'test_kind':'mock','full_length':True,'profile_mode':'practice','rules':valid_rules({'minutes':rules['minutes'],'correct':rules['correct'],'wrong':rules['wrong'],'skipped':0}),
            'questions':questions,'file_ids':sorted({r['file_id'] for q in questions for k in ('q_refs','s_refs') for r in q[k]}),
            'status':'draft','version':0,'revision':1,'source':'Owner-uploaded '+book.payload['filename'],'attribution':'Original book source; owner-confirmed content-use rights.',
            'rights_upload':True,'rights_publish':True,'rights_report':True,'audience':'all','allowed_emails':[],'allowed_phones':[],'expires':'',
            'live_enabled':True,'start_at':start,'competition':book.payload.get('competitive',False),'created_at':now(),'created_by':book.owner_id}
        if rules['mechanic']=='bitsat_bonus':data['rules']['bonus_rule']='answer_all_main_then_lock'
        if dest:
            from .structure import next_order
            if 'catalog_base' not in book.payload:book.payload['catalog_base']=await next_order(dest['section_id'])-1
            data.update(catalog_section_id=dest['section_id'],catalog_order=book.payload['catalog_base']+mock.order)
        if data['competition']:
            if mock.release_override:raise ValueError('An expired competitive window needs a new edition and future schedule.')
            from .live_window import window as live_window
            data['last_start_at'],data['end_at']=live_window(start,rules['minutes'],book.payload['closes_at'])
        await fence(book,token)
        await sets.update_one({'id':sid},{'$setOnInsert':data},upsert=True)
        await publish_validated(sid,{'confirm':True},await principal(book))
        if mock.set_id and mock.set_id!=sid:
            await sets.update_one({'id':mock.set_id,'book_import_id':book.id},{'$set':{'status':'withdrawn','live_enabled':False}})
            if mock.set_id not in mock.history:mock.history.append(mock.set_id)
        mock.set_id=sid;mock.published_generation=mock.generation;mock.publish_requested=False;mock.state='scheduled' if start>stamp else 'published';await save_mock(mock)
        book.payload.setdefault('metrics',{}).setdefault('first_ready_seconds',max(0,now()-book.created_at))
        await audit(book.owner_id,'Book mock published',sid,'Original keys and source evidence retained; previous attempts unchanged.')
