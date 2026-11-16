"""Chapter-wise PDFs: chapter headings, PDF bookmarks and subjects. Pure functions; no I/O and no AI."""
import re

WORDS = 'one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty'.split()
NUMBER = r'(?P<num>\d{1,3}|[ivxl]{1,6}|' + '|'.join(WORDS) + r')'
SUBJECTS = r'physics|chemistry|math(?:ematic)?s|biology|english|logical\s+reasoning'
SUBJECT_LINE = re.compile(rf'^(?:{SUBJECTS})$', re.I)
HEAD = re.compile(rf'^(?:(?P<subj>{SUBJECTS})\s*[-–—:|/·]?\s*)?(?:chapter(?:[- ]?wise)?(?:\s+(?:test|practice))?|ch\.?|unit|topic)\s*(?:no\.?\s*)?[-–—:#]?\s*{NUMBER}\b(?!\.\d)\.?\s*(?:[:\-–—|)/.·•]\s*)?(?P<title>.*)$', re.I)
ROLE_FIRST = re.compile(rf'^(?:(?:detailed|worked|hints?\s*(?:&|and))\s+)?(?P<role>solutions?|answers?\s*keys?|answers?)\s*(?:[:\-–—|·•]\s*|\s+(?:for|to|of)\s+)?(?:chapter|ch\.?|unit|topic)\s*(?:no\.?\s*)?[-–—:#]?\s*{NUMBER}\b(?!\.\d)\.?\s*(?:[:\-–—|(]\s*)?(?P<title>.*?)\)?$', re.I)
ROLE_TAIL = re.compile(r'(?:\s*[-–—:|/·•]\s*|\s*\(\s*|\s+(?=(?:answer\s*keys?|answer\s*sheet|hints?\s*(?:&|and)\s*solutions?|(?:detailed|worked)\s+solutions?)\b))((?:detailed\s+|worked\s+|hints?\s*(?:&|and)\s*)?solutions?|answers?(?:\s*keys?)?|answer\s*sheet)\s*\)?$', re.I)
ROLE_ONLY = re.compile(r'^(?:(?:detailed|worked|hints?\s*(?:&|and))\s+)?(solutions?|answers?(?:\s*keys?)?)$', re.I)
# 'Answer key – Sets Relations & Functions' / 'Solutions: Complex Numbers': a role heading that names its chapter instead of numbering it.
ROLE_NAMED = re.compile(r'^(?:(?:detailed|worked|hints?\s*(?:&|and))\s+)?(?P<role>solutions?|answers?\s*keys?|answers?)\s*[:\-–—|·•]\s*(?P<title>.+)$', re.I)
EXERCISE = re.compile(r'^(?P<word>exercise|level|part)\s*[-–—:#]?\s*(?P<id>\d{1,2}|[ivx]{1,4}|[a-d])\b(?!\.\d)\s*(?:[:.\-–—)]\s*.{0,60})?$', re.I)
FRONT = re.compile(r'^(?:contents|table of contents|index|preface|foreword|introduction|about|how to use|using this book|cover|title|copyright|acknowledg|answer|solution|hints?|appendix|formula|bibliography|references)', re.I)

# JEE Main / BITSAT / COMEDK chapter names and common aliases, for subjects and heading-only books.
SYLLABUS = {
    'Physics': ['Units and Measurements|Units and Dimensions|Units Dimensions and Errors|Physical World and Measurement|Measurement and Errors|Units and Measurement',
                'Kinematics|Motion in a Straight Line|Motion in One Dimension|Rectilinear Motion', 'Motion in a Plane|Motion in Two Dimensions|Projectile Motion|Relative Motion',
                'Laws of Motion|Newtons Laws of Motion|Newton s Laws of Motion|Friction', 'Circular Motion', 'Work Energy and Power|Work Power and Energy|Work Energy Power|Work and Energy',
                'Centre of Mass and Collisions|Centre of Mass|Center of Mass|Momentum and Collisions|Collisions|System of Particles|Centre of Mass and Momentum',
                'Rotational Motion|Rotational Dynamics|System of Particles and Rotational Motion|Rigid Body Dynamics', 'Gravitation',
                'Elasticity|Mechanical Properties of Solids|Properties of Solids', 'Fluid Mechanics|Mechanical Properties of Fluids|Fluids|Hydrostatics|Surface Tension|Viscosity',
                'Thermal Properties of Matter|Thermal Properties|Calorimetry|Thermal Expansion|Heat Transfer', 'Kinetic Theory of Gases|Kinetic Theory',
                'Oscillations|Simple Harmonic Motion', 'Waves|Wave Motion|Sound Waves|Sound',
                'Electrostatics|Electric Charges and Fields|Electric Field|Electric Potential|Electrostatic Potential|Gauss s Law',
                'Capacitance|Capacitors|Electrostatic Potential and Capacitance', 'Current Electricity',
                'Magnetic Effects of Current|Moving Charges and Magnetism|Magnetic Field|Magnetic Effect of Current|Biot Savart Law',
                'Magnetism and Matter|Magnetism|Magnetic Properties of Matter', 'Electromagnetic Induction|Faraday s Law', 'Alternating Current|AC Circuits',
                'Electromagnetic Waves|EM Waves', 'Ray Optics|Ray Optics and Optical Instruments|Geometrical Optics', 'Wave Optics|Interference and Diffraction',
                'Dual Nature of Matter and Radiation|Dual Nature of Radiation and Matter|Dual Nature|Photoelectric Effect', 'Atoms|Atomic Physics|Bohr Model',
                'Nuclei|Nuclear Physics|Radioactivity', 'Semiconductors|Semiconductor Electronics|Semiconductor Devices|Electronic Devices',
                'Communication Systems|Communication', 'Experimental Physics|Experimental Skills|Error Analysis', 'Thermodynamics', 'Vectors'],
    'Chemistry': ['Mole Concept|Some Basic Concepts of Chemistry|Stoichiometry|Basic Concepts of Chemistry', 'Atomic Structure|Structure of Atom',
                  'Periodic Table|Periodic Properties|Classification of Elements and Periodicity in Properties|Periodicity', 'Chemical Bonding|Chemical Bonding and Molecular Structure',
                  'States of Matter|Gaseous State|Gases and Liquids', 'Solid State|The Solid State|Solids', 'Thermochemistry|Chemical Thermodynamics|Thermodynamics and Thermochemistry|Thermodynamics',
                  'Chemical Equilibrium|Equilibrium', 'Ionic Equilibrium', 'Redox Reactions|Redox|Oxidation and Reduction', 'Solutions|Liquid Solutions',
                  'Electrochemistry', 'Chemical Kinetics', 'Surface Chemistry', 'Hydrogen', 's Block Elements|The s Block Elements',
                  'p Block Elements|The p Block Elements', 'd and f Block Elements|The d and f Block Elements|Transition Elements', 'Coordination Compounds|Coordination Chemistry',
                  'Metallurgy|General Principles and Processes of Isolation of Elements|Isolation of Elements', 'Environmental Chemistry',
                  'General Organic Chemistry|Organic Chemistry Some Basic Principles and Techniques|Some Basic Principles of Organic Chemistry', 'Isomerism',
                  'Hydrocarbons|Alkanes|Alkenes|Alkynes', 'Haloalkanes and Haloarenes|Alkyl Halides|Haloalkanes', 'Alcohols Phenols and Ethers|Alcohols|Phenols',
                  'Aldehydes Ketones and Carboxylic Acids|Aldehydes and Ketones|Carbonyl Compounds|Carboxylic Acids', 'Amines|Organic Compounds Containing Nitrogen|Nitrogen Compounds',
                  'Biomolecules', 'Polymers', 'Chemistry in Everyday Life', 'Practical Chemistry|Principles Related to Practical Chemistry|Purification and Characterisation of Organic Compounds|Qualitative Analysis',
                  'Nuclear Chemistry'],
    'Mathematics': ['Sets|Sets Relations and Functions', 'Relations and Functions|Functions|Relations', 'Complex Numbers|Complex Numbers and Quadratic Equations',
                    'Quadratic Equations|Theory of Equations', 'Matrices|Matrices and Determinants', 'Determinants', 'Permutations and Combinations|Permutation and Combination',
                    'Mathematical Induction|Principle of Mathematical Induction', 'Binomial Theorem', 'Sequences and Series|Sequence and Series|Progressions',
                    'Limits|Limits and Derivatives', 'Continuity and Differentiability|Limits Continuity and Differentiability|Continuity|Differentiability',
                    'Differentiation|Methods of Differentiation|Derivatives', 'Application of Derivatives|Applications of Derivatives',
                    'Indefinite Integration|Indefinite Integrals', 'Definite Integration|Definite Integrals', 'Area Under Curves|Application of Integrals|Applications of Integrals|Area Under the Curve',
                    'Differential Equations', 'Straight Lines|Straight Line', 'Circles|Circle', 'Conic Sections|Parabola|Ellipse|Hyperbola',
                    'Three Dimensional Geometry|3D Geometry|Introduction to Three Dimensional Geometry', 'Vector Algebra|Vectors and 3D|Vectors',
                    'Statistics', 'Probability', 'Trigonometry|Trigonometric Functions|Trigonometric Ratios and Identities|Trigonometric Equations',
                    'Inverse Trigonometric Functions|Inverse Trigonometry', 'Heights and Distances|Properties of Triangles', 'Mathematical Reasoning',
                    'Linear Programming', 'Linear Inequalities', 'Fundamentals of Mathematics|Basic Mathematics'],
}


def norm(text):
    text = re.sub(r'[’\']', ' ', str(text or '')).replace('&', ' and ')
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', text.lower()).split())


NAMES = {}
for _subject, _rows in SYLLABUS.items():
    for _row in _rows:
        for _alias in _row.split('|'):
            NAMES.setdefault(norm(_alias), set()).add(_subject)


def number_of(token):
    t = token.lower().rstrip('.')
    if t.isdigit():
        return int(t)
    if t in WORDS:
        return WORDS.index(t) + 1
    values = {'i': 1, 'v': 5, 'x': 10, 'l': 50}
    if not re.fullmatch(r'l?x{0,3}(?:ix|iv|v?i{0,3})', t) or not t:
        return None
    total, top = 0, 0
    for ch in reversed(t):
        n = values[ch]
        total, top = (total - n, top) if n < top else (total + n, n)
    return total


def canon_subject(name):
    n = norm(name)
    return {'maths': 'Mathematics', 'math': 'Mathematics', 'mathematics': 'Mathematics', 'logical reasoning': 'Logical reasoning'}.get(n, n.title() if n else '')


def match_subject(name, allowed):
    """The exam's own spelling of a subject ('Maths' and 'Mathematics' are one), or ''."""
    if not name:
        return ''
    want = canon_subject(name)
    for s in allowed:
        if canon_subject(s) == want:
            return s
    return ''


def syllabus_subject(title):
    found = NAMES.get(norm(title))
    return next(iter(found)) if found and len(found) == 1 else ''


def tidy(title):
    title = re.sub(r'\s*\.{2,}.*$', '', ' '.join(str(title or '').split())).strip(' -–—:|.')
    if title.isupper() and len(title) > 3:
        title = ' '.join(w if i and w in ('of', 'and', 'in', 'the', 'a', 'to', 'on') else w.capitalize() for i, w in enumerate(title.lower().split()))
    return title


def heading(value):
    """'Chapter 3: Kinematics', 'CHAPTER 03', 'Ch-2 Gravitation', 'Answer Key – Chapter 3' as {number, title, role, subject}; prose is never a heading."""
    v = ' '.join(value.split())
    if not v[:1].isupper() or len(v) > 110:
        return None
    m = ROLE_FIRST.match(v)
    role, subject = None, ''
    if m:
        role = 'solution' if 'solution' in m['role'].lower() else 'key'
    else:
        m = HEAD.match(v)
        if not m:
            return None
        subject = canon_subject(m['subj']) if m['subj'] else ''
    n = number_of(m['num'])
    if not n or not 1 <= n <= 300:
        return None
    title, bare = tidy(m['title']), False
    if title and not role:
        only = ROLE_ONLY.match(title)
        tail = ROLE_TAIL.search(title)
        if only:
            role = 'solution' if 'solution' in title.lower() else 'key'
            bare, title = role == 'solution' and norm(title) in ('solution', 'solutions'), title if norm(title) in ('solution', 'solutions') else ''
        elif tail and tail.start() > 0:
            role, title = ('solution' if 'solution' in tail[1].lower() else 'key'), tidy(title[:tail.start()])
    if title and (title[:1].islower() or len(title.split()) > 12 or re.match(r'^\d', title)):
        return None
    return {'number': n, 'title': title, 'role': role, 'subject': subject, 'bare_role': bare}


def name_heading(value):
    """A line that is just a syllabus chapter name, e.g. 'KINEMATICS' or 'Laws of Motion'; a wrapped '…Differentiability)' inside working is not."""
    v = ' '.join(value.split())
    if not v[:1].isupper() or len(v) > 70 or ROLE_ONLY.match(v) or SUBJECT_LINE.match(v) or re.search(r'[()\[\]{}]', v):
        return ''
    return tidy(v) if norm(v) in NAMES else ''


def named_role(value):
    """'Answer key – <chapter name>', '<chapter name> – Solutions' or 'Solutions: <chapter name>' as (role, title); the title must match a chapter already seen."""
    v = ' '.join(value.split())
    if not (v[:1].isupper() or v[:1].isdigit()) or len(v) > 110:
        return None
    m = ROLE_NAMED.match(v)
    if m:
        role, title = m['role'], m['title']
    else:
        tail = ROLE_TAIL.search(v)
        if not tail or tail.start() == 0:
            return None
        role, title = tail[1], v[:tail.start()]
    title = tidy(title)
    # '3D Geometry' may start with a digit: the caller accepts only a title that names a chapter already seen.
    if not title or not (title[:1].isupper() or title[:1].isdigit()) or len(title.split()) > 12:
        return None
    return ('solution' if 'solution' in role.lower() else 'key'), title


def label_for(known, number, title):
    if number:
        return f'Chapter {number}'
    want = norm(title)
    return next((lab for lab, rec in known.items() if want and norm(rec.get('title')) == want), '')


def title_line(lines, i, band, new=False):
    """The chapter name printed on the line just under 'Chapter 3'; a new chapter may be called 'Solutions'."""
    line = lines[i]
    for j in range(i + 1, min(i + 3, len(lines))):
        nxt = lines[j]
        text = ' '.join(nxt['text'].split())
        if band(nxt) or nxt['rect'][1] - line['rect'][3] > .06:
            return None
        if not text or not text[:1].isupper() or len(text) > 90 or (ROLE_ONLY.match(text) and not (new and norm(text) in ('solution', 'solutions'))) or SUBJECT_LINE.match(text) or heading(text):
            return None
        if re.match(r'^(?:Q(?:uestion)?\.?\s*)?\d{1,3}\s*[.):]', text) or re.match(r'^\(?[A-D]\)', text):
            return None
        return j
    return None


def find(lines, known, band):
    """Chapter headings on one page, top to bottom: dicts with y, label, role, record and the consumed line indexes."""
    known = {k: dict(v) for k, v in known.items()}
    numbered = any(v.get('number') for v in known.values())
    out, used = [], set()
    for i, line in enumerate(lines):
        if i in used:
            continue
        value = line['text'].strip()
        h, mine = heading(value), []
        if h is None:
            named = named_role(value)
            label = label_for(known, None, named[1]) if named else ''
            if label:
                out.append({'y': line['rect'][1], 'label': label, 'role': named[0], 'record': dict(known[label]), 'rows': [line['rect'][1]]})
                continue
            name = name_heading(value)
            label = label_for(known, None, name) if name else ''
            if not name or (not label and numbered):
                continue
            h = {'number': None, 'title': name, 'role': None, 'subject': '', 'bare_role': False}
            label = label or name
        else:
            if h['bare_role'] and f"Chapter {h['number']}" not in known:
                h.update(role=None, bare_role=False)
            elif h['bare_role']:
                h['title'] = ''
            if not h['title'] and not h['role']:
                j = title_line(lines, i, band, f"Chapter {h['number']}" not in known)
                if j is not None:
                    used.add(j)
                    mine.append(j)
                    h['title'] = tidy(lines[j]['text'])
            label = label_for(known, h['number'], h['title'])
            numbered = True
        for j in (i - 1, i + 1):
            if 0 <= j < len(lines) and j not in used and not band(lines[j]) and SUBJECT_LINE.match(lines[j]['text'].strip()) and abs(lines[j]['rect'][1] - line['rect'][1]) < .08:
                h['subject'] = h['subject'] or canon_subject(lines[j]['text'])
                used.add(j)
                mine.append(j)
        rec = known.setdefault(label, {})
        for k in ('number', 'title', 'subject'):
            if h.get(k) and not rec.get(k):
                rec[k] = h[k]
        out.append({'y': line['rect'][1], 'label': label, 'role': h['role'], 'record': dict(rec), 'rows': [line['rect'][1]] + [lines[j]['rect'][1] for j in mine]})
    return out, used


def exercise(value):
    v = ' '.join(value.split())
    m = EXERCISE.match(v) if v[:1].isupper() and len(v) < 70 else None
    return f"{m['word'].title()} {m['id'].upper()}" if m else ''


def plan_start(context, entry):
    """The reading context at a page where the owner (or the PDF's bookmarks) says a chapter part begins."""
    c = dict(context)
    c.update(mock=entry['label'], role=entry['role'], last={}, subject='Questions', numeric=False)
    c.pop('open_q', None)
    c.pop('open_s', None)
    info = {k: dict(v) for k, v in (c.get('chapter_info') or {}).items()}
    rec = info.setdefault(entry['label'], {})
    for k in ('number', 'title', 'subject'):
        if entry.get(k):
            rec[k] = entry[k]
    c['chapter_info'] = info
    return c


def labelled(chapters, starts):
    """Plan entries from chapters [{title, subject}] and starts [{page, chapter, role}]."""
    plan = []
    for s in sorted(starts, key=lambda s: (s['page'], {'question': 0, 'key': 1, 'solution': 2}[s['role']])):
        c = chapters[s['chapter']]
        plan.append({'page': s['page'], 'label': f"Chapter {s['chapter'] + 1}", 'number': s['chapter'] + 1, 'title': c['title'], 'subject': c.get('subject', ''), 'role': s['role']})
    return plan


def bookmark_plan(toc, pages):
    """Chapter starts from the PDF's own bookmarks: the outermost level that is not front matter, with subjects from parent bookmarks."""
    rows = [(int(l), ' '.join(str(t).split()), int(p)) for l, t, p in toc if 1 <= int(p) <= pages and str(t).strip()]
    subject, level_of_subject, found = '', None, []
    for level, title, page in rows:
        if SUBJECT_LINE.match(title):
            subject, level_of_subject = canon_subject(title), level
            continue
        if level_of_subject is not None and level <= level_of_subject:
            subject, level_of_subject = '', None
        if not FRONT.match(title):
            found.append((level, title, page, subject))
    if not found:
        return []
    top = min(r[0] for r in found)
    chosen = [r for r in found if r[0] == top]
    if len(chosen) == 1 and any(r[0] == top + 1 for r in found):
        chosen = [r for r in found if r[0] == top + 1]
    chapters, starts, pages_seen = [], [], set()
    for level, title, page, subj in sorted(chosen, key=lambda r: r[2]):
        if page in pages_seen:
            continue
        pages_seen.add(page)
        h = heading(title)
        chapters.append({'title': (h or {}).get('title') or tidy(title)[:120], 'subject': subj or (h or {}).get('subject', '')})
        starts.append({'page': page, 'chapter': len(chapters) - 1, 'role': 'question'})
    # Child bookmarks such as 'Answer key' or 'Solutions' under a chapter start that chapter's key or solutions.
    top_level, by_page, current = chosen[0][0], {s['page']: s['chapter'] for s in starts}, None
    for level, title, page in rows:
        if level == top_level and page in by_page:
            current = by_page[page]
        elif current is not None and level > top_level:
            role = ROLE_ONLY.match(title) or ROLE_TAIL.search(title) or ROLE_NAMED.match(title)
            if role and page >= starts[current]['page']:
                starts.append({'page': page, 'chapter': current, 'role': 'solution' if 'solution' in title.lower() else 'key'})
    return labelled(chapters, starts)[:300]


def bookmark_title(toc, page):
    """The PDF bookmark's name for a chapter starting on this page (or the page before)."""
    for _, title, p in toc:
        if page and p in (page - 1, page) and not FRONT.match(str(title)) and not SUBJECT_LINE.match(str(title).strip()):
            h = heading(str(title))
            return (h['title'] if h else tidy(title))[:120]
    return ''


def book_subjects(text):
    return {canon_subject(m) for m in re.findall(rf'\b({SUBJECTS})\b', str(text or '').replace('_', ' '), re.I)}


def resolve_subject(chain, allowed):
    """First source in the chain that names one of the exam's subjects: (subject, source) or ('', '')."""
    for value, source in chain:
        s = match_subject(value, allowed)
        if s:
            return s, source
    return '', ''
