from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool
from .db import db, now
from .book_models import BookPage, UploadPart, BookAllowance
from .book_store import load_book, lock_book, unlock, save_book, fence, original, digest, identity, enqueue_book, mocks_for
from .book_pdf import inspect
from .book_reader import read_page
from .book_publish import rebuild, publish_ready
from tejas_storage import put_object


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
        p=book.payload
        if book.state=='uploading':return 'Waiting for upload completion.'
        if not p.get('source_path'):
            chunks=[UploadPart.from_mongo(row) async for row in db.tejas_book_parts.find({'book_id':id}).sort('number',1)]
            raw=b''.join(c.data for c in chunks)
            if len(raw)!=p['size'] or digest(raw)!=p['sha256']:raise ValueError('Upload hash mismatch. Reselect the exact PDF and retry completed parts.')
            info=await run_in_threadpool(inspect,raw)
            p['source_path']=await run_in_threadpool(put_object,f'jeelive/books/{id}/original.pdf',raw,'application/pdf')
            p.update(pages=info['pages'],read_pages=0,scanned_pages=0,message='Original received privately. Reading pages in recoverable batches.')
            book.state='reading';await save_book(book,token)
        else:raw=await original(book)
        if p.get('read_pages',0)<p['pages']:
            previous=await db.tejas_book_pages.find_one({'book_id':id,'number':p.get('read_pages',0)})
            context=(previous or {}).get('context',{})
            for n in range(p.get('read_pages',0)+1,min(p['pages'],p.get('read_pages',0)+10)+1):
                await fence(book,token)
                existing=await db.tejas_book_pages.find_one({'_id':identity(id,'page',n)})
                if existing:
                    page=BookPage.from_mongo(existing);context=page.context
                else:
                    try:
                        data=await run_in_threadpool(inspect,raw,'text',n)
                        mapped,context=read_page(data['lines'],context,data.get('geometry',[]))
                        text='\n'.join(line['text'] for line in data['lines'])
                        page=BookPage(id=identity(id,'page',n),book_id=id,number=n,**mapped.model_dump(),text=text[:150000],scanned=not data['lines'],context=context,provenance={'kind':'native'})
                    except ValueError as exc:
                        page=BookPage(id=identity(id,'page',n),book_id=id,number=n,issues=[str(exc)],context=context)
                    await db.tejas_book_pages.update_one({'_id':page.id},{'$setOnInsert':page.to_mongo()},upsert=True)
                p['read_pages']=n;p['scanned_pages']=await db.tejas_book_pages.count_documents({'book_id':id,'scanned':True})
                p['message']=f'Read {n} of {p["pages"]} pages. Unclear content remains private.'
                await save_book(book,token)
            more=p['read_pages']<p['pages']
        if not more:
            allowance=await db.tejas_book_allowances.find_one({'book_id':id,'state':{'$in':['queued','running']}},sort=[('created_at',1)])
            if allowance:
                from .book_ai import process_allowance
                a=BookAllowance.from_mongo(allowance)
                a=await process_allowance(book,token,a,raw)
                await db.tejas_book_allowances.replace_one({'_id':a.id},a.to_mongo())
                more=a.state=='queued'
            book.state='matching';await save_book(book,token)
            await rebuild(book,token)
            for mock in await mocks_for(book):
                try:
                    await publish_ready(book,token,raw,mock.id)
                except (ValueError,HTTPException) as exc:
                    await fence(book,token)
                    mock.state='held';mock.issues=list(dict.fromkeys(mock.issues+[str(getattr(exc,'detail',exc))[:350]]))
                    from .book_store import save_mock
                    await save_mock(mock)
            mocks=await mocks_for(book)
            book.state='attention_needed' if not mocks or any(m.state=='held' for m in mocks) else 'published' if all(m.state in ('published','scheduled') for m in mocks) else 'ready'
            p['message']='Clean mocks are isolated from held content. Review the book map and Attention Needed queue.'
            p['metrics']={'native_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'native'}),
                'manually_repaired_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'owner_repair'}),
                'ai_proposed_pages':await db.tejas_book_pages.count_documents({'book_id':id,'provenance.kind':'ai_proposal'}),
                'blocking_issues':sum(len(m.issues) for m in mocks),**{k:v for k,v in p.get('metrics',{}).items() if k=='first_ready_seconds'}}
            more=more or bool(await db.tejas_book_allowances.find_one({'book_id':id,'state':'queued'}))
        await save_book(book,token)
    except Exception as exc:
        book.state='failed';book.payload['message']=str(exc.detail if isinstance(exc,HTTPException) else exc)[:350] if isinstance(exc,(ValueError,HTTPException)) else 'Processing interrupted. Retry resumes the saved pages without uploading again.'
        try:await save_book(book,token)
        except HTTPException:pass
        more=False
    finally:
        await unlock(book,token)
    if more:await enqueue_book(book)
    return 'Book batch saved.'


async def recover():
    rows=await db.tejas_books.find({'removed':False,'paused':False,'state':{'$in':['received','reading','matching']}}).limit(20).to_list(20)
    from .book_models import Book
    for row in rows:
        book=Book.from_mongo(row)
        await enqueue_book(book)
