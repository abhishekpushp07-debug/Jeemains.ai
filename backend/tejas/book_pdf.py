import base64, json, subprocess, sys, tempfile
from pathlib import Path


def inspect(raw, action='info', page=None, rect=None):
    if len(raw)>50*1024*1024 or not raw.startswith(b'%PDF-'):
        raise ValueError('Use a PDF within 50 MB.')
    with tempfile.TemporaryDirectory(prefix='book-private-') as tmp:
        root=Path(tmp)
        (root/'input.pdf').write_bytes(raw)
        (root/'request.json').write_text(json.dumps({'action':action,'page':page,'rect':rect}))
        try:
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('book_pdf_worker.py')),tmp],capture_output=True,timeout=45,
                env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'},close_fds=True,start_new_session=True)
        except subprocess.TimeoutExpired:
            raise ValueError('This page exceeded its safe processing time. Re-export it or repair its ranges.') from None
        if len(result.stdout)>12*1024*1024: raise ValueError('PDF output exceeded its safe budget.')
        try: data=json.loads(result.stdout)
        except ValueError: raise ValueError('PDF processing stopped safely. Original upload is retained.') from None
        if result.returncode or data.get('error'): raise ValueError(data.get('error','PDF processing stopped safely.'))
        if data.get('sandbox')!='chroot_low_uid_seccomp_resource_limits': raise ValueError('Parser isolation unavailable.')
        if 'image' in data: data['image_bytes']=base64.b64decode(data.pop('image'),validate=True)
        return data
