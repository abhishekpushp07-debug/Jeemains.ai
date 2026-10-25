import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path('/app/data/jee_pyq/source_audit')
MONTHS = {'january': 1, 'jan': 1, 'april': 4, 'apr': 4}


def position(row):
    return row['page'], row['column'], row['rect'][1]


def load_pages(fid, psm):
    files = sorted((ROOT / 'ocr' / fid).glob(f'*-psm{psm}.json'))
    pages = [json.loads(path.read_text()) for path in files]
    for page in pages:
        for column in page['columns']:
            for line in column['lines']:
                words = [w for w in line['words'] if not (len(w['text']) <= 2 and (w['rect'][0] <= column['left'] + 3 or w['rect'][2] >= column['right'] - 3))]
                while words and words[0]['text'] == '|':
                    words.pop(0)
                while words and words[-1]['text'] == '|':
                    words.pop()
                if words:
                    line['words'] = words
                    line['text'] = ' '.join(w['text'] for w in words)
                    line['rect'] = [min(w['rect'][0] for w in words), min(w['rect'][1] for w in words), max(w['rect'][2] for w in words), max(w['rect'][3] for w in words)]
    return pages


def metadata(pages):
    cover = pages[0]
    text = ' '.join(r['text'] for r in cover.get('cover_lines', [r for c in cover['columns'] for r in c['lines']]))
    match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(January|Jan|April|Apr)\s+(202\d)\s+Shift\s*[^\d]*(\d)', text, re.I)
    evidence = match[0] if match else ''
    if not match:
        printed = re.search(r'HELD ON.*?(\d{1,2})(?:st|nd|rd|th|d)?\s+(January|Jan|April|Apr)\s+(202\d)', text, re.I)
        timing = re.search(r'TIME\s*:\s*(9\s*[:.]\s*00\s*AM|3\s*[:.]\s*00\s*PM)\s+TO\s+(12\s*[:.]\s*00\s*(?:NOON|PM)|6\s*[:.]\s*00\s*PM)', text, re.I)
        if printed and timing:
            shift = '1' if timing[1].strip().startswith('9') else '2'
            match = [printed[0], printed[1], printed[2], printed[3], shift]
            evidence = printed[0] + ' · ' + timing[0]
    if not match or match[4] not in ('1', '2'):
        raise ValueError('Printed date/shift is not unambiguous')
    day = int(match[1])
    month = MONTHS[match[2].lower()]
    year = int(match[3])
    canonical_date = date(year, month, day).isoformat()
    return {'exam_date': canonical_date,
            'shift': int(match[4]), 'year': int(match[3]), 'date_evidence': evidence,
            'cover_page': 1, 'cover_text': text,
            'printed_75': bool(re.search(r'75\s+questions', text, re.I)),
            'printed_3_hours': bool(re.search(r'3\s*(hours|hrs)', text, re.I)),
            'printed_300': '300' in text}


def labels(pages):
    questions, answers, solutions, sections = [], [], [], []
    for page in pages:
        width, height = page['pdf_width'], page['pdf_height']
        for column in page['columns']:
            markers = [r['rect'][0] for r in column['lines'] if re.match(r'^(Ans|Sol)\b', r['text'], re.I)]
            margin = min(markers) + width * .009 if markers else width * (.09 if column['index'] == 0 else .53)
            for line in column['lines']:
                x, y, _, _ = line['rect']
                if y < height * .055 or y > height * .95:
                    continue
                row = {**line, 'page': page['page'], 'column': column['index']}
                raw = re.sub(r'^\d{1,2}\.\s*(?=Ans\b)', '', line['text'].strip(), flags=re.I)
                row['text'] = raw
                if re.match(r'^(MATHEMATICS|PHYSICS|CHEMISTRY|SECTION)', raw, re.I):
                    sections.append(row)
                q = re.match(r'^(\d{1,2})(?:[.,]\s*|\s+|$)', raw)
                beside_key = re.fullmatch(r'\d{1,2}\.', raw) and any(re.match(r'^Ans\b', other['text'], re.I) and abs(other['rect'][1] - y) < height * .006 for other in column['lines'])
                if x <= margin and q and 1 <= int(q[1]) <= 75 and not beside_key:
                    questions.append({**row, 'number': int(q[1])})
                if re.match(r'^Ans\b[.,:]?', raw, re.I):
                    marker = next((w for w in line['words'] if re.match(r'^Ans(?:[.,:]|$)', w['text'], re.I)), None)
                    if marker:
                        mid = (marker['rect'][1] + marker['rect'][3]) / 2
                        span = marker['rect'][3] - marker['rect'][1]
                        aligned = [w for w in line['words'] if w['rect'][0] >= marker['rect'][0] and abs((w['rect'][1] + w['rect'][3]) / 2 - mid) <= span * .75]
                        row['rect'] = [min(w['rect'][0] for w in aligned), min(w['rect'][1] for w in aligned), max(w['rect'][2] for w in aligned), max(w['rect'][3] for w in aligned)]
                        row['text'] = ' '.join(w['text'] for w in aligned)
                    answers.append(row)
                if x <= margin and re.match(r'^(Sol|Sok|So)[.,\s]', raw, re.I):
                    marker = next((w for w in line['words'] if re.match(r'^(Sol|Sok|So)(?:[.,:]|$)', w['text'], re.I)), None)
                    if marker:
                        marker_rect = list(marker['rect'])
                        for word in line['words']:
                            if re.fullmatch(r'\([+-]?\d+(?:,\d+)*\)', word['text']) and 0 <= word['rect'][0] - marker['rect'][2] < 20 and abs(word['rect'][1] - marker['rect'][1]) < 4:
                                marker_rect[2] = max(marker_rect[2], word['rect'][2])
                                marker_rect[3] = max(marker_rect[3], word['rect'][3])
                        row['rect'] = marker_rect
                    solutions.append(row)
    return tuple(sorted(rows, key=position) for rows in (questions, answers, solutions, sections))


def crop_refs(pages, start, end):
    refs = []
    for page in pages:
        for column in page['columns']:
            here = (page['page'], column['index'])
            if here < position(start)[:2] or here > position(end)[:2]:
                continue
            top = start['rect'][1] - 2 if here == position(start)[:2] else page['pdf_height'] * .07
            bottom = end['rect'][1] - 2 if here == position(end)[:2] else page['pdf_height'] * .96
            if bottom <= top + 2:
                continue
            refs.append({'page': page['page'], 'rect': [round(column['left'], 3), round(top, 3), round(column['right'], 3), round(bottom, 3)]})
    return refs


def extract(fid, psm=6):
    pages = load_pages(fid, psm)
    if not pages or pages[0]['page'] != 1:
        raise ValueError('Cover OCR is missing')
    if len(pages) != pages[0].get('total_pages') or any(p.get('schema') not in (2, 3) for p in pages):
        raise ValueError('Complete schema2 OCR is required before extracting a paper')
    source = (ROOT / (fid + '.pdf')).read_bytes()
    source_sha = hashlib.sha256(source).hexdigest()
    reviews_path = ROOT / 'visual_reviews.json'
    review = json.loads(reviews_path.read_text()).get(fid, {}) if reviews_path.exists() else {}
    if review and review.get('source_sha256') != source_sha:
        raise ValueError('Visual review does not match this source PDF hash')
    try:
        meta = metadata(pages)
    except ValueError:
        if not review.get('metadata'):
            raise
        meta = review['metadata']
    anchors, answers, solutions, sections = labels(pages)
    anchors = [a for a in anchors if not any(a['page'] == bad['page'] and a['column'] == bad['column'] and abs(a['rect'][1] - bad['y']) < 3 for bad in review.get('ignored_anchors', []))]
    repairs_path = ROOT / (fid + '.anchor_repairs.json')
    if repairs_path.exists():
        recovered = json.loads(repairs_path.read_text())
        if recovered['source_sha256'] != source_sha:
            raise ValueError('Recovered number glyphs belong to a different source')
        for row in recovered['repairs']:
            anchors = [a for a in anchors if not (position(a)[:2] == position(row)[:2] and abs(a['rect'][1] - row['rect'][1]) < 4)]
            anchors.append(row)
        anchors.sort(key=position)
    for number, checked in review.get('questions', {}).items():
        if checked.get('anchor'):
            row = {**checked['anchor'], 'number': int(number)}
            anchors = [a for a in anchors if not (position(a)[:2] == position(row)[:2] and abs(a['rect'][1] - row['rect'][1]) < 4)]
            anchors.append(row)
    anchors.sort(key=position)
    for anchor in anchors:
        checked = review.get('questions', {}).get(str(anchor['number']), {})
        if 'top' in checked:
            anchor['rect'] = [anchor['rect'][0], checked['top'], *anchor['rect'][2:]]
    counts = Counter(q['number'] for q in anchors)
    issues = []
    sequence = [q['number'] for q in anchors]
    if sequence != list(range(1, 76)):
        issues.append({'issue': 'question_sequence', 'missing': sorted(set(range(1, 76)) - set(sequence)),
                       'duplicate': {n: c for n, c in counts.items() if c != 1}, 'actual': sequence})
    output = []
    for index, anchor in enumerate(anchors):
        stop = anchors[index + 1] if index + 1 < len(anchors) else {'page': pages[-1]['page'], 'column': 1, 'rect': [0, pages[-1]['pdf_height'] * .94, 0, 0]}
        all_keys = [a for a in answers if position(anchor) < position(a) < position(stop)]
        sols = [s for s in solutions if position(anchor) < position(s) < position(stop)]
        checked = review.get('questions', {}).get(str(anchor['number']), {})
        keys = [a for a in all_keys if not sols or position(a) < position(sols[0])]
        if checked.get('key_anchor'):
            keys = [checked['key_anchor']]
        if not keys and sols and re.fullmatch(r'(?:Sol|Sok|So)[.,:]?\s*\([+-]?\d+\)', sols[0]['text'], re.I):
            keys = [sols[0]]
        q = {'number': anchor['number'], 'anchor': {'page': anchor['page'], 'column': anchor['column'], 'rect': anchor['rect'], 'text': anchor['text']}, 'key_evidence': [a['text'] for a in keys], 'issues': [], 'warnings': []}
        checked = review.get('questions', {}).get(str(anchor['number']), {})
        if len(all_keys) > len(keys):
            q['warnings'].append('Additional answer text appears inside the supplied worked solution; the primary key before Sol. is retained.')
        if checked.get('warning'):
            q['warnings'].append(checked['warning'])
        key = None
        accepted = []
        source_status = 'normal'
        if len(keys) == 1:
            printed = keys[0]['text'].strip().replace('−', '-')
            if re.fullmatch(r'Ans[.,:]?\s*\((?:Dropped|BONUS)\)', printed, re.I):
                source_status = 'dropped' if 'dropped' in printed.lower() else 'bonus'
                key = ''
            else:
                match = re.fullmatch(r'(?:Ans|Sol|Sok|So)[.,:]?\s*[\[(]?\s*([+-]?\d+(?:\s*,\s*[+-]?\d+)*)\s*[\])]?', printed, re.I)
                if match:
                    accepted = [str(int(value.strip())) for value in match[1].split(',')]
                    key = accepted[0]
        if checked.get('answer') is not None:
            if 'printed_answer' in checked:
                q['printed_answer'] = checked['printed_answer']
                q['normalization_evidence'] = checked.get('warning', checked.get('evidence', ''))
            key = str(checked['answer'])
            accepted = checked.get('accepted_answers', [key])
        if key is None:
            q['issues'].append('Printed answer key needs review')
        if not sols and not checked.get('solution_verified') and source_status == 'normal' and not checked.get('key_only'):
            q['issues'].append('Supplied solution label needs visual review')
        n = anchor['number']
        q.update(subject='Mathematics' if n <= 25 else 'Physics' if n <= 50 else 'Chemistry',
                 type='mcq' if (n - 1) % 25 < 20 else 'integer', answer=key, accepted_answers=accepted, source_status=source_status,
                 solution_kind='supplied_key_only' if checked.get('key_only') or source_status != 'normal' else 'supplied_worked')
        if q['type'] == 'mcq' and source_status == 'normal' and (not accepted or any(value not in ('1', '2', '3', '4') for value in accepted)):
            q['issues'].append('Single-choice key is not a supported source option')
        if len(keys) == 1:
            q['key_ref'] = checked.get('key_ref', {'page': keys[0]['page'], 'rect': keys[0]['rect']})
            split = checked.get('answer_boundary', keys[0])
            q['q_refs'] = crop_refs(pages, anchor, split)
            q['s_refs'] = crop_refs(pages, split, checked.get('solution_end', stop))
            for kind in ('q_refs', 's_refs'):
                excluded = checked.get('exclude_' + kind, [])
                q[kind] = [ref for index, ref in enumerate(q[kind]) if index not in excluded]
                for change in checked.get('adjust_' + kind, []):
                    q[kind][change['index']]['rect'] = change['rect']
                    if change.get('omit_rects'):
                        q[kind][change['index']]['omit_rects'] = change['omit_rects']
        if q['issues']:
            issues.append({'question': n, 'issues': q['issues']})
        output.append(q)
    return {'drive_id': fid, 'source_sha256': source_sha, 'metadata': meta,
            'ocr_pages': len(pages), 'questions': output, 'issues': issues,
            'counts': {'questions': len(anchors), 'answer_labels': len(answers), 'solution_labels': len(solutions)},
            'subject_section_evidence': [{'page': r['page'], 'text': r['text']} for r in sections],
            'status': 'REVIEW_REQUIRED', 'note': 'Candidate extraction only; no publication or completeness claim.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--psm', type=int, default=6)
    args = parser.parse_args()
    result = extract(args.file, args.psm)
    output = ROOT / (args.file + '.candidates.json')
    output.write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ('drive_id', 'counts', 'issues', 'subject_section_evidence')}, indent=2))
