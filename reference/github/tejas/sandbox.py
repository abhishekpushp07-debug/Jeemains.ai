"""Bounded, finite subprocess supervision for private PDF processing."""
import asyncio
import json
import os
from pathlib import Path
import tempfile
import shutil
import sys

BASE=Path('/app/backend/.processing-private')
MAX_PDF=50*1024*1024
MAX_OUTPUT=48*1024*1024


async def organise_pdfs(questions_path,solutions_path=None,format='pdf',chapter_book=False):
    BASE.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(BASE,0o700)
    directory=Path(tempfile.mkdtemp(prefix='organise-',dir=BASE))
    process=None
    try:
        for source,name in [(questions_path,'questions.'+format),(solutions_path,'solutions.'+format)]:
            if source is None: continue
            if Path(source).stat().st_size>MAX_PDF: raise ValueError('File exceeds 50 MB')
            shutil.copyfile(source,directory/name)
        env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'LANG':'C.UTF-8','PYTHONIOENCODING':'utf-8',
             'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
        script=Path(__file__).with_name('chapter_book_organiser_worker.py' if chapter_book else 'excel_organiser_worker.py' if format=='xlsx' else 'pdf_organiser_worker.py')
        process=await asyncio.create_subprocess_exec(sys.executable,str(script),str(directory),
            stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,
            env=env,close_fds=True,start_new_session=True)
        async def read():
            chunks=[]; size=0
            while True:
                chunk=await process.stdout.read(65536)
                if not chunk: break
                size+=len(chunk)
                if size>MAX_OUTPUT: raise ValueError('Organised output exceeds its safe size limit')
                chunks.append(chunk)
            await process.wait()
            return b''.join(chunks)
        raw=await asyncio.wait_for(read(),55)
        try: result=json.loads(raw)
        except (ValueError,UnicodeError): raise ValueError('PDF processing stopped safely. Try a smaller searchable PDF.')
        if process.returncode or result.get('error'):
            raise ValueError(result.get('error','PDF processing exceeded its resource budget'))
        if result.get('sandbox')!='chroot_low_uid_seccomp_resource_limits': raise ValueError('Required parser isolation was not established')
        return result
    except asyncio.TimeoutError:
        raise ValueError('PDF processing exceeded55seconds. Split the paper or export a searchable PDF.')
    finally:
        if process and process.returncode is None:
            process.kill(); await process.wait()
        shutil.rmtree(directory,ignore_errors=True)
