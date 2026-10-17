"""Automatic Office -> PDF conversion with a disposable restricted filesystem."""
import hashlib, os, re, shutil, subprocess, sys, tempfile, threading, zipfile, io
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
_RUNTIME=Path(os.environ.get('TEJAS_OFFICE_RUNTIME_DIR', '/var/cache/jeemains/office-runtime'))
_LOCK=threading.Lock()


def validate_office(raw, extension):
    if len(raw)>40*1024*1024:
        raise ValueError('Office documents must be under 40 MB.')
    if extension in ('docx','xlsx'):
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                entries=z.infolist()
                if len(entries)>15000 or sum(i.file_size for i in entries)>180*1024*1024:
                    raise ValueError('Document expands beyond the safe processing limit.')
                names={i.filename for i in entries}
                required='word/document.xml' if extension=='docx' else 'xl/workbook.xml'
                if required not in names or any('vbaproject' in n.lower() for n in names):
                    raise ValueError('Use a valid, macro-free Word/Excel document.')
        except zipfile.BadZipFile:
            raise ValueError('The Word/Excel document is not a valid Office file.') from None
    elif not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('The legacy Word/Excel signature is invalid.')


def _copy_file(source, root):
    source=Path(source)
    if not source.exists() or source.is_dir():return
    target=root/str(source).lstrip('/')
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():shutil.copy2(source.resolve(),target)


def runtime():
    with _LOCK:
        if (_RUNTIME/'.ready').exists() and (_RUNTIME/'.ready').read_text()=='office-jail-v3':return _RUNTIME
        binary=Path('/usr/lib/libreoffice/program/soffice.bin')
        if not binary.exists():raise ValueError('The document conversion runtime is unavailable. The upload remains private.')
        shutil.rmtree(_RUNTIME,ignore_errors=True);_RUNTIME.mkdir(parents=True)
        for source in ('/usr/lib/libreoffice','/usr/share/libreoffice','/usr/share/fonts','/usr/share/fontconfig','/etc/fonts','/etc/libreoffice','/var/lib/libreoffice/share/prereg','/var/spool/libreoffice/uno_packages/cache','/usr/share/poppler/cMap','/usr/lib/locale'):
            if Path(source).exists():shutil.copytree(source,_RUNTIME/source.lstrip('/'),symlinks=True,dirs_exist_ok=True)
        binaries=[binary]+list(Path('/usr/lib/libreoffice/program').glob('*.so*'))
        deps=set()
        for file in binaries:
            if file.is_file():
                result=subprocess.run(['ldd',str(file)],capture_output=True,text=True,timeout=10)
                deps.update(re.findall(r'(/[^\s()]+)',result.stdout))
        for lib in deps:_copy_file(lib,_RUNTIME)
        _copy_file('/lib64/ld-linux-x86-64.so.2',_RUNTIME)
        etc=_RUNTIME/'etc';etc.mkdir(exist_ok=True)
        (etc/'passwd').write_text('nobody:x:65534:65534:Document worker:/work:/bin/false\n')
        (etc/'group').write_text('nogroup:x:65534:\n')
        (etc/'nsswitch.conf').write_text('passwd: files\ngroup: files\nhosts: files\n')
        (_RUNTIME/'.ready').write_text('office-jail-v3')
        return _RUNTIME


def _link(source,destination):
    try:os.link(source,destination)
    except OSError:shutil.copy2(source,destination)


def convert(raw, extension):
    validate_office(raw,extension)
    base=runtime()
    with tempfile.TemporaryDirectory(prefix='jeemains-office-') as tmp:
        jail=Path(tmp)/'jail';shutil.copytree(base,jail,copy_function=_link,symlinks=True)
        source=jail/'input';source.mkdir();(source/('source.'+extension)).write_bytes(raw)
        for folder in ('work','work/tmp','work/out','work/profile','work/profile/user'):
            p=jail/folder;p.mkdir(exist_ok=True);os.chown(p,65534,65534);os.chmod(p,0o700)
        profile=jail/'work/profile/user/registrymodifications.xcu'
        profile.write_text('''<?xml version="1.0" encoding="UTF-8"?><oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel" oor:op="fuse"><value>3</value></prop></item><item oor:path="/org.openoffice.Office.Common/Load"><prop oor:name="UpdateLinks" oor:op="fuse"><value>2</value></prop></item></oor:items>''')
        os.chown(profile,65534,65534)
        try:
            run=subprocess.run([sys.executable,str(ROOT/'tejas/office_worker.py'),str(jail),extension],capture_output=True,timeout=65,env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
        except subprocess.TimeoutExpired:
            raise ValueError('Document conversion exceeded its time limit. No test was published.') from None
        output=jail/'work/out/source.pdf'
        if run.returncode!=0 or not output.exists():
            raise ValueError('This Office document could not be rendered safely. It may be encrypted, damaged or unsupported; no test was published.')
        data=output.read_bytes()
        if not data.startswith(b'%PDF-') or len(data)>64*1024*1024:
            raise ValueError('Document conversion did not produce a safe PDF.')
        return data
