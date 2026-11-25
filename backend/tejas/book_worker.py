from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from .db import db, now
from .book_models import BookPage, UploadPart, BookAllowance
from .book_store import lock_book, unlock, save_book, fence, renew, original, remember, digest, identity, enqueue_book, mocks_for, save_mock
from .book_pdf import inspect, inspect_many
from .book_reader import read_page, READER_VERSION
from .book_publish import rebuild, publish_ready
from .chapter_reader import plan_start, bookmark_plan
from anyio import from_thread
from .step_guard import beat, holds
from tejas_storage import put_object, StorageError, StorageWaiting, StorageStuck, SupabaseRefused

PAGES_PER_STEP=100
MOCKS_PER_STEP=5


async def extract(source, numbers, alive=None):
    items=[{'action':'text','page':n} for n in numbers]
    try:
        return await run_in_threadpool(inspect_many,source,items,10)
    except ValueError:
        results=[]
        for n in numbers:
            try:results.append(await run_in_threadpool(inspect,source,'text',n))
            except ValueError as exc:results.append({'error':str(exc)})
            if alive:alive()  # page by page is slow but alive
        return results


async def read_batch(book, token, source):
    id=book.id;p=book.payload;start=p.get('read_pages',0)
    numbers=list(range(start+1,min(p['pages'],start+PAGES_PER_STEP)+1))
    done={r['number'] async for r in db.tejas_book_pages.find({'book_id':id,'number':{'$in':numbers}},{'number':1})}
    missing=[n for n in numbers if n not in done]
    extracted=dict(zip(missing,await extract(source,missing,lambda:beat(id,'page read')))) if missing else {}
    await renew(book,token)
    previous=await db.tejas_book_pages.find_one({'book_id':id,'number':start})
    context=(previous or {}).get('context',{})
    if not start and p.get('single_mock'):context={'mock':p['single_mock'],'single':True,'subject':'General'}
    if not start and p.get('chapters'):context={'chapters':True,'plan':bool(p.get('chapter_plan'))}
    plan_at={}
    for e in p.get('chapter_plan') or []:plan_at.setdefault(e['page'],[]).append(e)
    for n in numbers:
        await fence(book,token)
        existing=await db.tejas_book_pages.find_one({'_id':identity(id,'page',n)})
        if existing:
            context=BookPage.from_mongo(existing).context;continue
        for e in plan_at.get(n,[]):context=plan_start(context,e)
        data=extracted[n]
        if data.get('error'):
            page=BookPage(id=identity(id,'page',n),book_id=id,number=n,issues=[data['error']],context=context,provenance={'kind':'native','reader':READER_VERSION})
        else:
            mapped,context=read_page(data['lines'],context,data.get('geometry',[]),data.get('images',[]))
            text='\n'.join(line['text'] for line in data['lines'])
            page=BookPage(id=identity(id,'page',n),book_id=id,number=n,**mapped.model_dump(),text=text[:150000],scanned=not data['lines'],context=context,provenance={'kind':'native','reader':READER_VERSION})
        await db.tejas_book_pages.update_one({'_id':page.id},{'$setOnInsert':page.to_mongo()},upsert=True)
    p['read_pages']=numbers[-1] if numbers else start
    p['scanned_pages']=await db.tejas_book_pages.count_documents({'book_id':id,'scanned':True})
    p['message']=f'Read {p["read_pages"]} of {p["pages"]} pages. Unclear content remains private.'
    await save_book(book,token)
    return p['read_pages']<p['pages']


async def publish_batch(book, token, source):
    if book.paused:return False
    # A mock whose picture Supabase returned is tried once in a round of batches: the book's other mocks go first, then the book waits its 15 minutes.
    published=0;returned=(book.payload.get('stuck_round') or {}).get('mocks') or {}
    wanted=[m for m in await mocks_for(book) if (book.payload.get('auto_publish') or m.publish_requested) and m.state=='ready' and not m.issues and m.published_generation!=m.generation]
    for mock in wanted:
        if mock.id in returned:continue
        if published>=MOCKS_PER_STEP:return True
        try:
            await publish_ready(book,token,source,mock.id)
        except HTTPException as exc:
            if exc.status_code==409:raise
            await hold(book,token,mock,exc.detail)
        except StorageWaiting as exc:
            if exc.scope!='stuck':raise  # Supabase is away: the whole book waits for it and carries on; the mock is not held
            # One picture that Supabase keeps returning: only this mock waits (it stays Draft, nothing to fix in it); the book's other mocks carry on.
            returned[mock.id]={'mock':((mock.chapter or {}).get('title') or mock.label)[:120],'error':str(exc)[:300],'code':exc.code,'reason':exc.reason[:200],'next':exc.step[:240]}
            book.payload.setdefault('stuck_round',{'since':None})['mocks']=returned
        except (ValueError,StorageError) as exc:
            # One mock that cannot be saved waits for the owner's next Publish; the book and its other mocks carry on.
            await hold(book,token,mock,exc)
        published+=1
    left={m.id:returned[m.id] for m in wanted if m.id in returned}
    since=(book.payload.pop('stuck_round',None) or {}).get('since')
    if not left:return False
    # The round is over: the book says "Atki hai" with each stuck mock and its reason; they are tried again every 15 minutes or on Dobara chalao.
    first=next(iter(left.values()))
    exc=StorageStuck(first['error']);exc.code,exc.reason,exc.step,exc.mocks,exc.since=first['code'],first['reason'],first['next'],left,since
    raise exc


async def hold(book, token, mock, reason):
    await fence(book,token)
    mock.publish_hold=str(reason)[:350]
    mock.state='held';mock.issues=list(dict.fromkeys(mock.issues+[mock.publish_hold]))
    await save_mock(mock)


def use_bookmark_parts(p):
    """Bookmarks that mark every chapter's answer key or solutions describe the book exactly: read it by them from the start (an owner's own plan wins)."""
    if not p.get('chapters') or p.get('plan_source') == 'owner':
        return False
    plan = bookmark_plan(p.get('bookmarks') or [], p['pages'])
    chapters = {e['label'] for e in plan}
    if len(chapters) >= 2 and {e['label'] for e in plan if e['role'] != 'question'} == chapters and p.get('chapter_plan') != plan:
        p.update(chapter_plan=plan, plan_source='bookmarks')
        return True
    return False


async def relabel_kept(id, plan, published):
    """Pages kept across a switch to the bookmark plan (owner repairs, AI-approved pages) move to the bookmark chapter whose pages hold them."""
    starts = sorted((e['page'], e['label']) for e in plan)
    async for row in db.tejas_book_pages.find({'book_id': id, 'number': {'$nin': published}}):
        label = next((lab for page, lab in reversed(starts) if page <= row['number']), None)
        if not label:
            continue
        regions = [{**r, 'mock': label} for r in row.get('regions', [])]
        context = {**(row.get('context') or {}), 'plan': True, 'mock': label}
        await db.tejas_book_pages.update_one({'_id': row['_id']}, {'$set': {'regions': regions, 'context': context}})


async def receive(book, token):
    p=book.payload
    chunks=[UploadPart.from_mongo(row) async for row in db.tejas_book_parts.find({'book_id':book.id}).sort('number',1)]
    raw=b''.join(c.data for c in chunks);del chunks
    if len(raw)!=p['size'] or digest(raw)!=p['sha256']:raise ValueError('Upload hash mismatch. Reselect the exact PDF and retry completed parts.')
    source=await run_in_threadpool(remember,raw,p['sha256'])
    info=await run_in_threadpool(inspect,source)
    if p.get('chapters'):
        try:p['bookmarks']=(await run_in_threadpool(inspect,source,'toc'))['toc'][:1000]
        except ValueError:p['bookmarks']=[]
    async def keep(info):
        await db.tejas_books.update_one({'_id':book.id},{'$set':{'payload.transfer':info}})
    def progress(info):  # every 6 MB piece: the owner sees the %, and a later try carries on from Supabase's own offset
        beat(book.id,'piece sent');p['transfer']=info;from_thread.run(keep,info)
    p['source_path']=await run_in_threadpool(put_object,f'jeelive/books/{book.id}/original.pdf',raw,'application/pdf',p.get('transfer'),progress)
    p.pop('transfer',None)
    p.update(pages=info['pages'],read_pages=0,scanned_pages=0,reader_version=READER_VERSION,message='Original received privately. Reading pages in recoverable batches.')
    use_bookmark_parts(p)
    book.state='reading';await save_book(book,token)
    await db.tejas_book_parts.delete_many({'book_id':book.id})
    return source


async def step(job):
    id=job['payload']['book_id']
    try:book,token=await lock_book(id)
    except HTTPException as exc:
        # an upload whose access was removed, or that the owner deleted for good, has nothing left to do
        if exc.status_code==404 or not await db.tejas_books.find_one({'_id':id,'removed':False},{'_id':1}):return 'Book access removed.'
        raise
    holds(id,token);more=False;waited=None
    try:
        await fence(book,token)
        if book.paused:return 'Book paused by owner.'
        if await db.tejas_books.find_one({'_id':id,'archived':True},{'_id':1}):return 'Book is in the Library.'
        p=book.payload;waited=p.pop('storage_wait',None)
        if waited and waited.get('mocks'):p['stuck_round']={'since':waited['since'],'mocks':{}}  # a new round: every stuck mock is tried again; "since" is kept
        if book.state=='uploading':return 'Waiting for upload completion.'
        source=await receive(book,token) if not p.get('source_path') else await original(book)
        if p.get('reader_version')!=READER_VERSION:
            # Books read by an older page reader are re-read automatically; owner repairs, AI-approved pages and pages of published mocks are kept.
            published=sorted({n for m in await mocks_for(book) if m.published_generation for numbers in m.pages.values() for n in numbers})
            await db.tejas_book_pages.delete_many({'book_id':id,'number':{'$nin':published},'provenance.kind':{'$nin':['owner_repair','ai_proposal']},'provenance.reader':{'$ne':READER_VERSION}})
            p.update(read_pages=0,reader_version=READER_VERSION,rereading=True,message='Re-reading pages with the improved reader. Owner repairs are kept.')
            if use_bookmark_parts(p):
                # The chapters are now named by the PDF's bookmarks: copies under the old names that never reached students are rebuilt, not left held.
                await db.tejas_book_mocks.delete_many({'book_id':id,'published_generation':0,'set_id':None,'series_date':None,'release_at':None,'live_exam':False})
                await relabel_kept(id,p['chapter_plan'],published)
            book.state='reading';await save_book(book,token)
        if p.get('read_pages',0)<p['pages']:
            more=await read_batch(book,token,source)
        marks_needed=False
        if not more and not p.get('single_checked'):
            # A PDF with no printed mock heading is one paper: read it again as a single mock named after the upload.
            p['single_checked']=True
            labelled=await db.tejas_book_pages.find_one({'book_id':id,'regions.mock':{'$nin':['',None]}},{'_id':1})
            items=await db.tejas_book_pages.find_one({'book_id':id,'regions.role':{'$in':['question','key','solution']}},{'_id':1})
            if items and not labelled and p.get('chapters'):
                # No printed chapter headings: the PDF's own bookmarks split it, otherwise the owner marks where each chapter starts.
                plan=bookmark_plan(p.get('bookmarks') or [],p['pages']) if not p.get('chapter_plan') else []
                if plan:
                    p.update(chapter_plan=plan,plan_source='bookmarks',read_pages=0,message='No printed chapter headings. Splitting chapters by the PDF bookmarks.')
                    await db.tejas_book_pages.delete_many({'book_id':id,'provenance.kind':'native'})
                    book.state='reading';await save_book(book,token);more=True
                else:
                    marks_needed=True;book.state='chapters_needed'
                    p['message']='Chapter headings were not found. Mark the page where each chapter starts.'
            elif items and not labelled:
                p.update(single_mock=p['title'][:100],read_pages=0,message='One paper found. Reading it as a single mock.')
                await db.tejas_book_pages.delete_many({'book_id':id,'provenance.kind':'native'})
                book.state='reading';await save_book(book,token);more=True
        if not more and not marks_needed:
            allowance=await db.tejas_book_allowances.find_one({'book_id':id,'state':{'$in':['queued','running']}},sort=[('created_at',1)])
            if allowance:
                from .book_ai import process_allowance
                a=await process_allowance(book,token,BookAllowance.from_mongo(allowance),source)
                await db.tejas_book_allowances.replace_one({'_id':a.id},a.to_mongo())
                more=a.state=='queued'
            book.state='matching';await save_book(book,token)
            cutting=await rebuild(book,token,source)
            if not cutting:p.pop('rereading',None)  # fresh counts are in: Master shows them again
            await renew(book,token)
            more=cutting or await publish_batch(book,token,source) or more
            mocks=await mocks_for(book)
            book.state='matching' if more else 'attention_needed' if not mocks or any(m.state=='held' for m in mocks) else 'published' if all(m.state in ('published','scheduled') for m in mocks) else 'ready'
            published=sum(m.state in ('published','scheduled') for m in mocks)
            p['message']=('Cutting every question into its question and its options. Mocks arrive one by one.' if cutting else
                f'Publishing clean mocks in batches: {published} of {len(mocks)} released so far.' if more else
                'Clean mocks are isolated from held content. Review the book map and Attention Needed queue.')
            p['metrics']={'native_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'native'}),
                'manually_repaired_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'owner_repair'}),
                'ai_proposed_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'ai_proposal'}),
                'blocking_issues':sum(len(m.issues) for m in mocks),**{k:v for k,v in p.get('metrics',{}).items() if k=='first_ready_seconds'}}
            more=more or bool(await db.tejas_book_allowances.find_one({'book_id':id,'state':'queued'}))
        p.pop('hang',None)  # a finished step: the count of silent steps in a row starts again
        await save_book(book,token)
    except Exception as exc:
        if isinstance(exc,HTTPException) and exc.status_code==409:raise  # another batch took this PDF: the job waits its turn, the book is not marked failed
        if isinstance(exc,StorageWaiting):
            # Supabase is away: the book keeps its state and saved work, shows that it waits, and the job runs again by itself.
            # One file that Supabase keeps returning ("Atki hai") stops alone and says why; other books carry on.
            stuck=exc.scope=='stuck';mocks=getattr(exc,'mocks',None) or {};what=next(iter(mocks.values()),{}).get('mock','');base=book.payload.get('catalog_base')
            first=(book.payload.get('metrics') or {}).get('first_ready_seconds')
            extra=f' aur {len(mocks)-1} doosre mock' if len(mocks)>1 else ''
            await db.tejas_books.update_one({'_id':id},{'$set':{'payload.storage_wait':{'since':getattr(exc,'since',None) or (waited or {}).get('since') or now(),'at':now(),'error':str(exc)[:300],
                    'kind':exc.scope,'code':exc.code,'reason':exc.reason[:200],'next':exc.step[:240],**({'stuck':True} if stuck else {}),
                    **({'mock':what,'mock_id':next(iter(mocks)),'mocks':{i:{'mock':v['mock'],'reason':v['reason']} for i,v in mocks.items()}} if mocks else {})},
                # what the mocks published in this batch changed in the book is kept: their place in the list, the time the first one was ready
                **({'payload.catalog_base':base} if base is not None else {}),**({'payload.metrics.first_ready_seconds':first} if stuck and first is not None else {}),
                'payload.message':(f'Atki hai: "{what}"{extra} ki picture Supabase mein nahi ja rahi. Baaki mock aur kitaabein chal rahi hain.' if what else
                    'Atki hai: yeh file Supabase mein nahi ja rahi. File surakshit hai; baaki kitaabein chal rahi hain.') if stuck else
                    'Supabase ka intezaar. File surakshit hai; Supabase lautte hi yahin se aage chalega.'},
                # the next round tries every stuck mock again; the re-read that finished before the stuck picture stays finished
                # this step was not silent: the count of silent steps in a row starts again
                '$unset':{'payload.hang':'',**({'payload.stuck_round':'',**({} if 'rereading' in book.payload else {'payload.rereading':''})} if stuck else {})}})
            raise
        import logging;logging.getLogger(__name__).exception('Book step failed (book=%s)',id)
        book.payload.pop('stuck_round',None);book.payload.pop('hang',None)
        book.state='failed';book.payload['message']=str(exc.detail if isinstance(exc,HTTPException) else exc)[:350] if isinstance(exc,(ValueError,HTTPException,SupabaseRefused)) else 'Processing interrupted. Retry resumes the saved pages without uploading again.'
        try:await save_book(book,token)
        except HTTPException:pass
        more=False
    finally:
        await unlock(book,token)
    if more:await enqueue_book(book)
    return 'Book batch saved.'


async def recover():
    rows=await db.tejas_books.find({'removed':False,'paused':False,'$or':[{'state':{'$in':['received','reading','matching']}},
        {'state':{'$in':['attention_needed','ready']},'payload.reader_version':{'$ne':READER_VERSION}}]}).limit(20).to_list(20)
    from .book_models import Book
    for row in rows:
        # A book that waits for Supabase, or whose file is stuck, already has its own waiting job: a second one would only try it more often.
        if row['payload'].get('storage_wait') and await db.tejas_jobs.find_one({'kind':'book_step','payload.book_id':row['_id'],'status':{'$in':['queued','running']}},{'_id':1}):continue
        await enqueue_book(Book.from_mongo(row))
