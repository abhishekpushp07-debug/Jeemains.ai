"""TEST-ONLY: write the synthetic iso170 3-mock book to /tmp/syn170.pdf (same layout the isolated book suites upload)."""
import fitz

INSTR = ['JEE Main Instructions', 'Duration: 180 minutes', 'Total Questions: {n}', 'Correct: +4', 'Wrong: -1',
         'Unanswered: 0', 'All questions are compulsory', 'No worked solutions; answer key only.']


def q3(tag):
    return [(1, f'{tag}: a ball falls 20 m. Find time.', ['1 s', '2 s', '3 s', '4 s']),
            (2, f'{tag}: unit of force is', ['joule', 'newton', 'watt', 'pascal']),
            (3, f'{tag}: speed of light order', ['1e3', '1e5', '1e8', '1e10'])]


doc = fitz.open()
p = doc.new_page(); p.insert_text((40, 60), 'Contents', fontsize=14)
p.insert_text((40, 90), 'This practice book contains labelled synthetic papers with answer keys.', fontsize=10)
for n, keys in ((1, [(1, 'B'), (2, 'B'), (3, 'C')]), (2, [(1, 'B'), (2, 'B'), (3, 'C')]), (3, [(1, 'B'), (2, 'B'), (2, 'A'), (3, 'C')])):
    p = doc.new_page(); p.insert_text((40, 60), f'Mock Test {n}', fontsize=14); y = 90
    for line in INSTR:
        p.insert_text((40, y), line.format(n=3), fontsize=11); y += 20
    p = doc.new_page(); p.insert_text((40, 60), 'Physics', fontsize=13); y = 100
    for num, text, opts in q3(f'S{n}'):
        p.insert_text((40, y), f'Q{num}. {text}', fontsize=11); y += 20
        for lab, o in zip('ABCD', opts):
            p.insert_text((60, y), f'({lab}) {o}', fontsize=11); y += 18
        y += 22
    p = doc.new_page(); p.insert_text((40, 60), 'Answer Key', fontsize=13); y = 100
    for num, ans in keys:
        p.insert_text((40, y), f'Q{num}. ({ans})', fontsize=11); y += 20
open('/tmp/syn170.pdf', 'wb').write(doc.tobytes())
print('pages', len(doc))
