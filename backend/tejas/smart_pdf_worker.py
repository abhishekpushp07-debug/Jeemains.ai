"""One-shot sealed PDF inspection/rendering for the smart upload pipeline."""
import base64,json,sys,os,codecs,unicodedata
from pathlib import Path
from pdf_organiser_worker import seal,open_pdf
import fitz

def main():
    directory=Path(sys.argv[1]);raw=(directory/'input.pdf').read_bytes();request=json.loads((directory/'request.json').read_text())
    # Warm encoders before sealing filesystem
    json.dumps({'text':'हिन्दी'},ensure_ascii=False).encode('utf-8')
    unicodedata.normalize('NFC','test')
    codecs.lookup('raw_unicode_escape')
    codecs.lookup('unicode_escape')
    seal(str(directory));doc=open_pdf(raw)
    action=request['action']
    result={'sandbox':'chroot_low_uid_seccomp_resource_limits'}
    if action=='info':
        result.update(pages=len(doc),first_text=('\n'.join(doc[i].get_text() for i in range(min(3,len(doc)))))[:45000])
    else:
        page_number=int(request['page'])
        if not 1<=page_number<=len(doc):raise ValueError('Page is outside the source document.')
        page=doc[page_number-1];clip=None
        if action=='crop':
            rect=request['rect']
            if len(rect)!=4 or not all(isinstance(x,(float,int)) and 0<=x<=1 for x in rect) or rect[0]>=rect[2] or rect[1]>=rect[3]:raise ValueError('Invalid normalized source rectangle.')
            clip=fitz.Rect(rect[0]*page.rect.width,rect[1]*page.rect.height,rect[2]*page.rect.width,rect[3]*page.rect.height)
        pix=page.get_pixmap(matrix=fitz.Matrix(1.7 if action=='page' else 2,1.7 if action=='page' else 2),clip=clip,alpha=False)
        data=pix.tobytes('png')
        if len(data)>8*1024*1024:raise ValueError('Rendered source exceeds8MB.')
        result.update(image=base64.b64encode(data).decode(),width=pix.width,height=pix.height,
                      text=page.get_text(clip=clip)[:22000])
    print(json.dumps(result,separators=(',',':')))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(json.dumps({'error':str(exc)[:400]}));sys.exit(1)
