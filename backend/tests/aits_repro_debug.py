import sys
sys.path.insert(0, '/app/backend')
import fitz
from tejas.book_pdf_worker import handle
from tejas.book_reader import read_page

doc = fitz.open(sys.argv[1] if len(sys.argv) > 1 else '/tmp/aits_1_25.pdf')
last = int(sys.argv[2]) if len(sys.argv) > 2 else 160
show = {int(x) for x in sys.argv[3].split(',')} if len(sys.argv) > 3 else {4, 5, 6, 29, 80, 81, 82, 155, 156, 157}
context, counts = {}, {}
for n in range(1, last + 1):
    data = handle(doc, {'action': 'text', 'page': n})
    mapped, context = read_page(data['lines'], context, data.get('geometry', []), data.get('images', []))
    counts[mapped.classification] = counts.get(mapped.classification, 0) + 1
    if n in show:
        print(f'== p{n} {mapped.classification} ctx role={context.get("role")} subj={context.get("subject")} mock={context.get("mock")}')
        print('   issues:', mapped.issues[:4])
        for r in mapped.regions[:3]:
            print('   ', r.role, r.mock, r.subject, r.number, [round(x, 3) for x in r.rect], r.response_type, r.answer, r.option_labels, r.checked, r.complete, repr(r.text[:60]))
print(counts)
