import base64, codecs, json, sys, unicodedata
from pathlib import Path
import fitz
import numpy as np
from pdf_organiser_worker import seal
from book_cutter import cut_region, trim_region, cut_boxes, textpage, pixmap

LIMIT=100*1024*1024


def visible_drawings(page):
    """Drawing boxes trimmed to their clip paths, so clipped-away strokes do not count as printed content."""
    out=[];clips={}
    # The C-level list is the same drawings as get_drawings(extended=True), several times cheaper to read.
    for d in page.get_cdrawings(extended=True)[:4000]:
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


def visible_images(page, images, lines, drawn):
    """Image boxes that really show on the page: a PDF may place pictures that its clip paths hide completely."""
    if not images:
        return []
    # Only the part of the page the pictures cover is drawn; the page's paper colour comes from a small picture of the whole page.
    pr = page.rect
    u = fitz.Rect(images[0])
    for b in images[1:]:
        u |= fitz.Rect(b)
    u = fitz.IRect(int(np.floor(max(pr.x0, u.x0 - 3))), int(np.floor(max(pr.y0, u.y0 - 3))), int(np.ceil(min(pr.x1, u.x1 + 3))), int(np.ceil(min(pr.y1, u.y1 + 3))))
    if u.is_empty:
        return []
    small = pixmap(page, matrix=fitz.Matrix(.25, .25), colorspace=fitz.csGRAY, alpha=False)
    back = int(np.bincount(np.frombuffer(small.samples, dtype=np.uint8).reshape(small.height, small.stride)[:, :small.width].ravel(), minlength=256).argmax())
    pix = pixmap(page, colorspace=fitz.csGRAY, alpha=False, clip=fitz.Rect(u))
    gray = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.stride)[:, :pix.width]
    ox, oy = pix.x, pix.y
    ink = np.abs(gray.astype(np.int16) - back) > 24
    H, W = ink.shape
    def wipe(x0, y0, x1, y1, pad):
        ink[max(0, int(y0 - pad) - oy):max(0, min(H + oy, int(y1 + pad) + 1) - oy), max(0, int(x0 - pad) - ox):max(0, min(W + ox, int(x1 + pad) + 1) - ox)] = False
    for x0, y0, x1, y1 in lines:
        wipe(x0, y0, x1, y1, 2)
    for x0, y0, x1, y1 in drawn:
        if x1 - x0 < 4 or y1 - y0 < 4:
            wipe(x0, y0, x1, y1, 2)
        else:
            for side in ((x0, y0, x1, y0), (x0, y1, x1, y1), (x0, y0, x0, y1), (x1, y0, x1, y1)):
                wipe(*side, 2)
    out = []
    PW, PH = int(np.ceil(pr.width)), int(np.ceil(pr.height))
    for b in images:
        x0, y0, x1, y1 = max(0, int(b[0])), max(0, int(b[1])), min(PW, int(b[2]) + 1), min(PH, int(b[3]) + 1)
        part = ink[max(0, y0 - oy):max(0, y1 - oy), max(0, x0 - ox):max(0, x1 - ox)] if x1 > x0 and y1 > y0 else None
        if part is not None and int(part.sum()) > max(12, .002 * (x1 - x0) * (y1 - y0)):
            if b[0] < -2 or b[1] < -2 or b[2] > PW + 2 or b[3] > PH + 2:
                # A picture placed partly off the page is cut down by a clip path: its box is where its ink really is.
                ys, xs = np.flatnonzero(part.any(axis=1)), np.flatnonzero(part.any(axis=0))
                b = [max(x0, ox) + int(xs[0]), max(y0, oy) + int(ys[0]), max(x0, ox) + int(xs[-1]) + 1, max(y0, oy) + int(ys[-1]) + 1]
            out.append(b)
    return out


def paint(page, clip, scale, erase):
    """One piece of a question; ruled borders and the printed option label inside it are painted white."""
    w, h = page.rect.width, page.rect.height
    pix = pixmap(page, matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
    for e in erase[:40]:
        if len(e) != 4 or not all(isinstance(x, (int, float)) for x in e):
            raise ValueError('Invalid crop.')
        # Page coordinates straight to pixels, one pixel generous, so no sliver of a border survives at the edge of the piece.
        box = fitz.IRect(int(np.floor(e[0] * w * scale)) - 1, int(np.floor(e[1] * h * scale)) - 1,
                         int(np.ceil(e[2] * w * scale)) + 1, int(np.ceil(e[3] * h * scale)) + 1) & pix.irect
        if not box.is_empty:
            pix.set_rect(box, (255, 255, 255))
    return pix


def handle(doc, item):
    action=item.get('action')
    if action=='info':
        sample=min(10,len(doc))
        return {'pages':len(doc),'sampled_pages':sample,'scanned_sample':sum(len(doc[i].get_text().strip())<30 for i in range(sample))}
    if action=='toc':
        return {'toc':[[int(l),str(t)[:160],int(p)] for l,t,p in doc.get_toc(simple=True)[:2000]]}
    n=item.get('page')
    if not isinstance(n,int) or not 1<=n<=len(doc): raise ValueError('Page outside the book.')
    page=doc[n-1];w,h=page.rect.width,page.rect.height
    if not 1<=w<=4000 or not 1<=h<=4000: raise ValueError('Unsupported page dimensions; export standard pages.')
    if action=='text':
        lines=[]
        for block in page.get_text('dict',textpage=textpage(page,page.rect,fitz.TEXTFLAGS_DICT&~fitz.TEXT_PRESERVE_IMAGES))['blocks']:
            for line in block.get('lines',[]):
                text=''.join(s['text'] for s in line['spans']).strip()
                if text:
                    x0,y0,x1,y1=line['bbox']
                    lines.append({'text':text,'rect':[max(0,x0/w),max(0,y0/h),min(1,x1/w),min(1,y1/h)]})
        if sum(len(x['text']) for x in lines)>150000: raise ValueError('Page text exceeds safe processing budget.')
        drawn=visible_drawings(page)
        images=visible_images(page,[list(i['bbox']) for i in page.get_image_info()],[[x['rect'][0]*w,x['rect'][1]*h,x['rect'][2]*w,x['rect'][3]*h] for x in lines],drawn)
        geometry=images+drawn
        scale=lambda rows:[[max(0,r[0]/w),max(0,r[1]/h),min(1,r[2]/w),min(1,r[3]/h)] for r in rows]
        return {'lines':lines,'width':w,'height':h,'geometry':scale(geometry),'images':scale(images)}
    r=item.get('rect') or [0,0,1,1]
    if len(r)!=4 or not all(isinstance(x,(int,float)) for x in r) or not (0<=r[0]<r[2]<=1 and 0<=r[1]<r[3]<=1): raise ValueError('Invalid crop.')
    labels=item.get('labels') or []
    if action in ('cut','boxes') and not (isinstance(labels,list) and len(labels)<=8 and all(isinstance(x,str) and len(x)==1 for x in labels)): raise ValueError('Invalid option labels.')
    typed=item.get('typed') or []
    if not (isinstance(typed,list) and all(x in labels for x in typed)): raise ValueError('Invalid option labels.')
    if action=='cut': return {'cut':cut_region(page,r,labels,typed) if labels else trim_region(page,r)}
    if action=='boxes': return {'cut':cut_boxes(page,r,item.get('boxes') or {},labels)}
    clip=fitz.Rect(r[0]*w,r[1]*h,r[2]*w,r[3]*h)
    if action=='piece':
        scale=item.get('scale')
        if not isinstance(scale,(int,float)) or not .2<=scale<=2: raise ValueError('Invalid crop.')
        pix=paint(page,clip,scale,item.get('erase') or [])
        data=pix.tobytes('png')
        if len(data)>8*1024*1024: raise ValueError('Page image exceeds safe budget.')
        return {'image':base64.b64encode(data).decode(),'width':pix.width,'height':pix.height}
    if action=='clip_text': return {'text':page.get_text(clip=clip)[:30000]}
    if action not in ('crop','page','thumb'): raise ValueError('Unsupported PDF action.')
    scale=min(1,820/clip.width) if action=='thumb' else min(2,1800/clip.width,2400/clip.height)
    pix=pixmap(page,matrix=fitz.Matrix(scale,scale),clip=clip,alpha=False)
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
