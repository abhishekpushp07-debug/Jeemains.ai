import base64, codecs, json, sys, unicodedata
from pathlib import Path
import fitz
from pdf_organiser_worker import seal

LIMIT=100*1024*1024


def visible_drawings(page):
    """Drawing boxes trimmed to their clip paths, so clipped-away strokes do not count as printed content."""
    out=[];clips={}
    for d in page.get_drawings(extended=True)[:4000]:
        level=d.get('level',0)
        for k in [k for k in clips if k>=level]:del clips[k]
        if d.get('type')=='clip':
            clips[level]=d.get('scissor') or d['rect'];continue
        if d.get('type')=='group':continue
        x0,y0,x1,y1=d['rect']
        for c in clips.values():x0,y0,x1,y1=max(x0,c[0]),max(y0,c[1]),min(x1,c[2]),min(y1,c[3])
        if x1>=x0 and y1>=y0:out.append([x0,y0,x1,y1])
        if len(out)>=2000:break
    return out


def handle(doc, item):
    action=item.get('action')
    if action=='info':
        sample=min(10,len(doc))
        return {'pages':len(doc),'sampled_pages':sample,'scanned_sample':sum(len(doc[i].get_text().strip())<30 for i in range(sample))}
    n=item.get('page')
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
        images=[list(i['bbox']) for i in page.get_image_info()]
        geometry=images+visible_drawings(page)
        scale=lambda rows:[[max(0,r[0]/w),max(0,r[1]/h),min(1,r[2]/w),min(1,r[3]/h)] for r in rows]
        return {'lines':lines,'width':w,'height':h,'geometry':scale(geometry),'images':scale(images)}
    r=item.get('rect') or [0,0,1,1]
    if len(r)!=4 or not all(isinstance(x,(int,float)) for x in r) or not (0<=r[0]<r[2]<=1 and 0<=r[1]<r[3]<=1): raise ValueError('Invalid crop.')
    clip=fitz.Rect(r[0]*w,r[1]*h,r[2]*w,r[3]*h)
    if action=='clip_text': return {'text':page.get_text(clip=clip)[:30000]}
    if action not in ('crop','page'): raise ValueError('Unsupported PDF action.')
    scale=min(2,1800/clip.width,2400/clip.height)
    pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),clip=clip,alpha=False)
    data=pix.tobytes('png')
    if len(data)>8*1024*1024: raise ValueError('Page image exceeds safe budget.')
    return {'image':base64.b64encode(data).decode(),'width':pix.width,'height':pix.height,'text':page.get_text(clip=clip)[:30000]}


def main():
    root=Path(sys.argv[1]); raw=(root/'input.pdf').read_bytes()
    request=json.loads((root/'request.json').read_text())
    codecs.lookup('raw_unicode_escape'); codecs.lookup('unicode_escape')
    unicodedata.normalize('NFC','test'); json.dumps({'text':'हिन्दी'}).encode()
    seal(str(root))
    if not raw.startswith(b'%PDF-') or len(raw)>LIMIT:
        raise ValueError('Use an unlocked PDF within 100 MB.')
    doc=fitz.open(stream=raw,filetype='pdf')
    if doc.is_encrypted or len(doc)<1:
        raise ValueError('Use an unlocked PDF with at least one page.')
    results=[]
    for item in request['items'][:40]:
        try: results.append(handle(doc,item))
        except Exception as exc: results.append({'error':str(exc)[:350]})
    print(json.dumps({'sandbox':'chroot_low_uid_seccomp_resource_limits','pages':len(doc),'results':results},separators=(',',':')))


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'error':str(exc)[:350]}));sys.exit(1)
