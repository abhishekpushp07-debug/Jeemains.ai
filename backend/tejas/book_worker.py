from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from .db import db
from .book_models import BookPage, UploadPart, BookAllowance
from .book_store import lock_book, unlock, save_book, fence, renew, original, remember, digest, identity, enqueue_book, mocks_for, save_mock
from .book_pdf import inspect, inspect_many
from .book_reader import read_page, READER_VERSION
from .book_publish import rebuild, publish_ready
from .chapter_reader import plan_start, bookmark_plan
from tejas_storage import put_object

PAGES_PER_STEP=20
MOCKS_PER_STEP=5


async def extract(source, numbers):
    items=[{'action':'text','page':n} for n in numbers]
    try:
        return await run_in_threadpool(inspect_many,source,items,10)
    except ValueError:
        results=[]
        for n in numbers:
            try:results.append(await run_in_threadpool(inspect,source,'text',n))
            except ValueError as exc:results.append({'error':str(exc)})
        return results


async def read_batch(book, token, source):
    id=book.id;p=book.payload;start=p.get('read_pages',0)
    numbers=list(range(start+1,min(p['pages'],start+PAGES_PER_STEP)+1))
    done={r['number'] async for r in db.tejas_book_pages.find({'book_id':id,'number':{'$in':numbers}},{'number':1})}
    missing=[n for n in numbers if n not in done]
    extracted=dict(zip(missing,await extract(source,missing))) if missing else {}
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
    published=0
    for mock in await mocks_for(book):
        if not (book.payload.get('auto_publish') or mock.publish_requested):continue
        if mock.state!='ready' or mock.issues or mock.published_generation==mock.generation:continue
        if published>=MOCKS_PER_STEP:return True
        try:
            await publish_ready(book,token,source,mock.id)
        except HTTPException as exc:
            if exc.status_code==409:raise
            await hold(book,token,mock,exc.detail)
        except ValueError as exc:
            await hold(book,token,mock,exc)
        published+=1
    return False


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
    p['source_path']=await run_in_threadpool(put_object,f'jeelive/books/{book.id}/original.pdf',raw,'application/pdf')
    p.update(pages=info['pages'],read_pages=0,scanned_pages=0,reader_version=READER_VERSION,message='Original received privately. Reading pages in recoverable batches.')
    use_bookmark_parts(p)
    book.state='reading';await save_book(book,token)
    await db.tejas_book_parts.delete_many({'book_id':book.id})
    return source


async def step(job):
    id=job['payload']['book_id']
    try:book,token=await lock_book(id)
    except HTTPException as exc:
        if exc.status_code==404:return 'Book access removed.'
        raise
    more=False
    try:
        await fence(book,token)
        if book.paused:return 'Book paused by owner.'
        if await db.tejas_books.find_one({'_id':id,'archived':True},{'_id':1}):return 'Book is in the Library.'
        p=book.payload
        if book.state=='uploading':return 'Waiting for upload completion.'
        source=await receive(book,token) if not p.get('source_path') else await original(book)
        if p.get('reader_version')!=READER_VERSION:
            # Books read by an older page reader are re-read automatically; owner repairs, AI-approved pages and pages of published mocks are kept.
            published=sorted({n for m in await mocks_for(book) if m.published_generation for numbers in m.pages.values() for n in numbers})
            await db.tejas_book_pages.delete_many({'book_id':id,'number':{'$nin':published},'provenance.kind':{'$nin':['owner_repair','ai_proposal']},'provenance.reader':{'$ne':READER_VERSION}})
            p.update(read_pages=0,reader_version=READER_VERSION,message='Re-reading pages with the improved reader. Owner repairs are kept.')
            if use_bookmark_parts(p):
                # The chapters are now named by the PDF's bookmarks: copies under the old names that never reached students are rebuilt, not left held.
                await db.tejas_book_mocks.delete_many({'book_id':id,'published_generation':0,'set_id':None,'series_date':None,'release_at':None,'live_exam':False})
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
            await rebuild(book,token)
            await renew(book,token)
            more=await publish_batch(book,token,source) or more
            mocks=await mocks_for(book)
            book.state='matching' if more else 'attention_needed' if not mocks or any(m.state=='held' for m in mocks) else 'published' if all(m.state in ('published','scheduled') for m in mocks) else 'ready'
            published=sum(m.state in ('published','scheduled') for m in mocks)
            p['message']=(f'Publishing clean mocks in batches: {published} of {len(mocks)} released so far.' if more else
                'Clean mocks are isolated from held content. Review the book map and Attention Needed queue.')
            p['metrics']={'native_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'native'}),
                'manually_repaired_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'owner_repair'}),
                'ai_proposed_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'ai_proposal'}),
                'blocking_issues':sum(len(m.issues) for m in mocks),**{k:v for k,v in p.get('metrics',{}).items() if k=='first_ready_seconds'}}
            more=more or bool(await db.tejas_book_allowances.find_one({'book_id':id,'state':'queued'}))
        await save_book(book,token)
    except Exception as exc:
        import logging;logging.getLogger(__name__).exception('Book step failed (book=%s)',id)
        book.state='failed';book.payload['message']=str(exc.detail if isinstance(exc,HTTPException) else exc)[:350] if isinstance(exc,(ValueError,HTTPException)) else 'Processing interrupted. Retry resumes the saved pages without uploading again.'
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
        await enqueue_book(Book.from_mongo(row))
