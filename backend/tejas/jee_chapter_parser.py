import re
import fitz


def normalise(value):
    return value.replace('−', '-').replace('–', '-').strip()


def lines(page):
    return [(line['bbox'], ''.join(span['text'] for span in line['spans']).strip())
            for block in page.get_text('dict')['blocks'] for line in block.get('lines', [])]


def chapter_outline(doc):
    cover = doc[0].get_text()
    subject = next((s for s in ('Chemistry', 'Mathematics', 'Physics') if re.search(r'^'+s+r'\s*$', cover, re.M)), None)
    info = re.search(r'(\d+) chapters / (\d+) questions / (\d+) minutes per chapter', cover)
    if not subject or 'JEE Main Chapter Tests' not in cover or not info:
        raise ValueError('Expected the supplied JEE Main chapter-test book format.')
    toc = doc.get_toc()
    starts = [(title, page-1) for depth, title, page in toc if depth == 1]
    if len(starts) != int(info[1]) or int(info[2]) != len(starts)*50 or not 1 <= len(starts) <= 60:
        raise ValueError('Cover counts and chapter bookmarks disagree.')
    return subject, int(info[3]), starts


def key_table(page):
    text = page.get_text()
    block = text.split('Answer key\n', 1)[1].split('Worked solutions and insights', 1)[0]
    tokens = normalise(block).split()
    if len(tokens) != 100 or [tokens[i] for i in range(0, 100, 2)] != [str(i) for i in range(1, 51)]:
        raise ValueError('Answer-key reading order is incomplete or ambiguous.')
    keys = {i+1: tokens[i*2+1] for i in range(50)}
    headings = {t: b for b, t in lines(page) if t in ('Answer key', 'Worked solutions and insights')}
    words = [w for w in page.get_text('words') if headings['Answer key'][3] < w[1] < headings['Worked solutions and insights'][1]]
    rows = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        row = next((r for r in rows if abs(r[0][1]-w[1]) < 1), None)
        if row is None: rows.append([w])
        else: row.append(w)
    geometric = {}
    for row in rows:
        row.sort(key=lambda w: w[0])
        if len(row) != 10: raise ValueError('Answer-key geometry must contain five complete pairs per row.')
        for i in range(0, 10, 2):
            n = int(row[i][4])
            if n in geometric: raise ValueError('Duplicate source-key number.')
            geometric[n] = normalise(row[i+1][4])
    if geometric != keys: raise ValueError('Independent key-table readings disagree.')
    return keys


def anchors(doc, start, stop):
    found = []
    for pi in range(start, stop):
        for box, text in lines(doc[pi]):
            match = re.fullmatch(r'Q(\d{1,2})\.', text)
            if match and 45 <= box[0] <= 65 and box[1] > 45:
                found.append({'number': int(match[1]), 'page': pi, 'top': max(45, box[1]-4)})
    if [a['number'] for a in found] != list(range(1, 51)):
        raise ValueError(f'Expected source question/solution sequence 1–50; found {len(found)} anchors.')
    return found


def regions(doc, start, end):
    refs, texts = [], []
    if end['page']-start['page'] > 8: raise ValueError('Source item spans too many pages.')
    for pi in range(start['page'], min(end['page']+1, len(doc))):
        page = doc[pi]
        top = start['top'] if pi == start['page'] else 45
        bottom = end['top'] if pi == end['page'] else page.rect.height-45
        if bottom <= top: continue
        rect = fitz.Rect(45, top, page.rect.width-45, bottom)
        text = page.get_text(clip=rect).strip()
        if not text: continue
        refs.append({'page': pi+1, 'rect': [round(v, 3) for v in rect]})
        texts.append(text)
    if not refs: raise ValueError('Source item has no readable crop.')
    return refs, '\n'.join(texts)


def parse_jee_book(doc):
    subject, duration, outline = chapter_outline(doc)
    chapters = []
    for ix, (title, start) in enumerate(outline):
        number = ix+1
        stop = outline[ix+1][1] if ix+1 < len(outline) else len(doc)
        intro = doc[start].get_text()
        if not re.search(r'^Chapter '+str(number)+r'\s*$', intro, re.M) or title not in intro:
            raise ValueError(f'Chapter {number}: bookmark and printed heading disagree.')
        spec = re.search(r'50 questions / (\d+) minutes / Maximum 200 marks', intro)
        types = re.search(r'(\d+) single-correct questions and (\d+) integer-response questions', intro)
        if not spec or int(spec[1]) != duration or not types or int(types[1])+int(types[2]) != 50:
            raise ValueError(f'Chapter {number}: duration, marks or response counts are missing.')
        key_pages = [p for p in range(start, stop) if re.search(r'^Answer key\s*$', doc[p].get_text(), re.M)]
        if len(key_pages) != 1: raise ValueError(f'Chapter {number}: expected exactly one source-key table.')
        kp = key_pages[0]
        keys = key_table(doc[kp])
        questions, worked = anchors(doc, start, kp), anchors(doc, kp, stop)
        parsed = []
        for idx, q in enumerate(questions):
            qrefs, qtext = regions(doc, q, questions[idx+1] if idx < 49 else {'page': kp, 'top': 45})
            srefs, stext = regions(doc, worked[idx], worked[idx+1] if idx < 49 else {'page': stop, 'top': 45})
            answer = re.search(r'Answer:\s*([A-D]|[+-]?\d+)\s*/\s*10-mark solution', normalise(stext))
            if not answer or answer[1] != keys[q['number']]:
                raise ValueError(f'{subject} chapter {number} Q{q["number"]}: solution answer does not match both key reads.')
            labels = re.findall(r'^Q(\d{1,2})\.', qtext, re.M)
            slabels = re.findall(r'^Q(\d{1,2})\.', stext, re.M)
            if labels != [str(q['number'])] or slabels != [str(q['number'])]:
                raise ValueError(f'Chapter {number} Q{q["number"]}: source regions overlap another item.')
            kind = 'integer' if re.search(r'^Integer response\s*$', qtext, re.M) else 'mcq' if re.search(r'^Single correct\s*$', qtext, re.M) else None
            key = keys[q['number']]
            if kind == 'mcq' and (key not in 'ABCD' or set(re.findall(r'\(([A-D])\)', qtext)) != set('ABCD')):
                raise ValueError(f'Chapter {number} Q{q["number"]}: missing options or incompatible key.')
            if not kind or (kind == 'integer' and not re.fullmatch(r'[+-]?\d+', key)):
                raise ValueError(f'Chapter {number} Q{q["number"]}: unsupported response or key.')
            if sum(map(int, re.findall(r'\[(\d+) marks?\]', stext))) != 10 or not all(label in stext for label in ('Insight:', 'Trap:', 'Quick check:')):
                raise ValueError(f'Chapter {number} Q{q["number"]}: incomplete supplied worked solution.')
            parsed.append({'number': q['number'], 'subject': subject, 'section': title, 'topic': title, 'type': kind,
                'text': qtext, 'answer': key, 'options': {c: 'See original option '+c for c in 'ABCD'} if kind == 'mcq' else {},
                'solution': stext, 'solution_number': q['number'], 'render_mode': 'source', 'solution_kind': 'supplied_worked',
                'accessible_text': 'Original PDF question. Source images preserve notation; extracted text is not a verified accessible transcription.',
                'solution_accessible_text': 'Supplied worked solution, teaching rubric, insight, trap and quick check. Teaching marks do not affect the +4/−1/0 test score.',
                'q_refs': qrefs, 's_refs': srefs, 'approved': False, 'issues': []})
        mcq = sum(q['type'] == 'mcq' for q in parsed)
        if (mcq, 50-mcq) != (int(types[1]), int(types[2])): raise ValueError('Extracted response counts differ from chapter instructions.')
        chapters.append({'number': number, 'title': title, 'start_page': start+1, 'end_page': stop, 'key_page': kp+1,
            'minutes': duration, 'questions': parsed,
            'verification': {'questions': 50, 'keys': 50, 'options': 50, 'mcq': mcq, 'integer': 50-mcq,
                'worked_solutions': 50, 'key_checks_agree': True, 'solution_keys_agree': True, 'source_images': True, 'issues': []}})
    return {'exam': 'JEE Main', 'subject': subject, 'minutes': duration, 'solution_kind': 'supplied_worked',
        'chapters': chapters, 'pages': len(doc), 'count': len(chapters)*50, 'parser_version': 'jee-chapter-worked-v1',
        'sandbox': 'chroot_low_uid_seccomp_resource_limits'}
