import base64, json, os, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LIMIT=100*1024*1024


def cpus():
    """The CPUs this server may really use (its container limit), not the machine's count."""
    try:
        quota,period=open('/sys/fs/cgroup/cpu.max').read().split()
        if quota!='max':return max(1,int(quota)//int(period))
    except (OSError,ValueError):pass
    return max(1,len(os.sched_getaffinity(0)))


LANES=min(8,max(2,cpus()))


def run(source, items):
    source=Path(source)
    # Every use marks the cached original as in use, so the cache never removes it while work on it is still going on.
    try: os.utime(source);size=source.stat().st_size
    except FileNotFoundError: raise ValueError('The cached original was refreshed. Retry; saved progress is kept.') from None
    if not 0<size<=LIMIT:
        raise ValueError('Use a PDF within 100 MB.')
    with tempfile.TemporaryDirectory(prefix='book-private-') as tmp:
        root=Path(tmp)
        try: os.link(source,root/'input.pdf')
        except FileNotFoundError: raise ValueError('The cached original was refreshed. Retry; saved progress is kept.') from None
        except OSError: shutil.copyfile(source,root/'input.pdf')
        (root/'request.json').write_text(json.dumps({'items':items}))
        try:
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('book_pdf_worker.py')),tmp],capture_output=True,timeout=90,
                env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},close_fds=True,start_new_session=True)
        except subprocess.TimeoutExpired:
            raise ValueError('This page exceeded its safe processing time. Re-export it or repair its ranges.') from None
        if len(result.stdout)>160*1024*1024: raise ValueError('PDF output exceeded its safe budget.')
        try: data=json.loads(result.stdout)
        except ValueError: raise ValueError('PDF processing stopped safely. Original upload is retained.') from None
        if result.returncode or data.get('error'): raise ValueError(data.get('error','PDF processing stopped safely.'))
        if data.get('sandbox')!='chroot_low_uid_seccomp_resource_limits': raise ValueError('Parser isolation unavailable.')
        results=data['results']
        if len(results)!=len(items): raise ValueError('PDF processing returned incomplete results.')
        for item in results:
            if 'image' in item: item['image_bytes']=base64.b64decode(item.pop('image'),validate=True)
        return results


def inspect(source, action='info', page=None, rect=None):
    result=run(source,[{'action':action,'page':page,'rect':rect}])[0]
    if result.get('error'): raise ValueError(result['error'])
    return result


def inspect_many(source, items, size=10):
    """Items in groups of `size`; the groups run side by side, one PDF worker per CPU, and come back in order."""
    groups=[items[start:start+size] for start in range(0,len(items),size)]
    if len(groups)<2:
        return [r for g in groups for r in run(source,g)]
    with ThreadPoolExecutor(max_workers=min(LANES,len(groups))) as pool:
        return [r for done in pool.map(lambda g:run(source,g),groups) for r in done]
