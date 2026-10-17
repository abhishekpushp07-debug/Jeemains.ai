"""Bounded PDF worker RPC. All untrusted PDF parsing stays in the sealed worker."""
import base64,json,os,subprocess,sys,tempfile
from pathlib import Path

def inspect(raw,action='info',page=None,rect=None):
    if not raw.startswith(b'%PDF-') or len(raw)>50*1024*1024:raise ValueError('Use a PDF under50MB.')
    with tempfile.TemporaryDirectory(prefix='jeemains-pdf-') as tmp:
        root=Path(tmp);(root/'input.pdf').write_bytes(raw)
        (root/'request.json').write_text(json.dumps({'action':action,'page':page,'rect':rect}))
        try:
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('smart_pdf_worker.py')),tmp],capture_output=True,timeout=55,
                env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','PYTHONIOENCODING':'utf-8','PYTHONDONTWRITEBYTECODE':'1'},close_fds=True,start_new_session=True)
        except subprocess.TimeoutExpired:raise ValueError('PDF processing exceeded its safe time limit.') from None
        if len(result.stdout)>12*1024*1024:raise ValueError('PDF worker output exceeds its safe budget.')
        try:data=json.loads(result.stdout)
        except ValueError:raise ValueError('PDF processing stopped safely; no content was published.') from None
        if result.returncode or data.get('error'):raise ValueError(data.get('error','PDF could not be processed.'))
        if data.get('sandbox')!='chroot_low_uid_seccomp_resource_limits':raise ValueError('PDF parser confinement was not established.')
        if 'image' in data:data['image_bytes']=base64.b64decode(data.pop('image'),validate=True)
        return data
