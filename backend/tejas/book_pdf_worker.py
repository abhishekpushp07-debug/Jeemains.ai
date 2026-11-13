import base64, codecs, json, sys, unicodedata
from pathlib import Path
import fitz
from pdf_organiser_worker import seal


def main():
    root=Path(sys.argv[1]); raw=(root/'input.pdf').read_bytes()
    request=json.loads((root/'request.json').read_text())
    codecs.lookup('raw_unicode_escape'); codecs.lookup('unicode_escape')
    unicodedata.normalize('NFC','test'); json.dumps({'text':'हिन्दी'}).encode()
    seal(str(root))
    if not raw.startswith(b'%PDF-') or len(raw)>50*1024*1024:
        raise ValueError('Use an unlocked PDF within 50 MB.')
    doc=fitz.open(stream=raw,filetype='pdf')
    if doc.is_encrypted or not 1<=len(doc)<=1000:
        raise ValueError('Use an unlocked book of 1–1,000 pages.')
    result={'sandbox':'chroot_low_uid_seccomp_resource_limits','pages':len(doc)}
    action=request['action']
    if action=='info':
        result['sampled_pages']=min(10,len(doc))
        result['scanned_sample']=sum(len(doc[i].get_text().strip())<30 for i in range(min(10,len(doc))))
    else:
        n=request['page']
        if not isinstance(n,int) or not 1<=n<=len(doc): raise ValueError('Page outside the book.')
        page=doc[n-1];w,h=page.rect.width,page.rect.height
        if not 1<=w<=4000 or not 1<=h<=4000: raise ValueError('Unsupported page dimensions; export standard pages.')
        if action=='text':
            lines=[]
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    text=''.join(s['text'] for s in line['spans']).strip()
                    if text:
                        x0,y0,x1,y1=line['bbox']
                        lines.append({'text':text,'rect':[max(0,x0/w),max(0,y0/h),min(1,x1/w),min(1,y1/h)]})
            if sum(len(x['text']) for x in lines)>150000: raise ValueError('Page text exceeds safe processing budget.')
            geometry=[list(i['bbox']) for i in page.get_image_info()]
            geometry.extend(list(d['rect']) for d in page.get_drawings()[:2000])
            geometry=[[max(0,r[0]/w),max(0,r[1]/h),min(1,r[2]/w),min(1,r[3]/h)] for r in geometry]
            result.update(lines=lines,width=w,height=h,geometry=geometry)
        else:
            r=request.get('rect') or [0,0,1,1]
            if len(r)!=4 or not 0<=r[0]<r[2]<=1 or not 0<=r[1]<r[3]<=1: raise ValueError('Invalid crop.')
            clip=fitz.Rect(r[0]*w,r[1]*h,r[2]*w,r[3]*h)
            scale=min(2,1800/clip.width,2400/clip.height)
            pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip,alpha=False)
            data=pix.tobytes('png')
            if len(data)>8*1024*1024: raise ValueError('Page image exceeds safe budget.')
            result.update(image=base64.b64encode(data).decode(),width=pix.width,height=pix.height,text=page.get_text(clip=clip)[:30000])
    print(json.dumps(result,separators=(',',':')))


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'error':str(exc)[:350]}));sys.exit(1)
