"""Evidence gate for real-exam rank context: missing mappings never become invented ranks."""
from collections import Counter
from fastapi import APIRouter, Depends
from .auth import current
from .learning_progress import released, family

router = APIRouter(prefix='/api/attempts', tags=['Historical rank evidence'])
REFERENCES = {
    'JEE Main': {'checked_year': 2026, 'title': 'NTA official notices and result documents',
        'url': 'https://jeemain.nta.nic.in/documents/',
        'reason': 'Raw marks do not identify a unique national rank. Shift normalization, NTA percentile, best-session rules and candidate distribution matter. No approved compatible marks-to-percentile/rank mapping is available.',
        'source_scope': 'Official examination/result notices; not a raw-marks-to-rank lookup table.'},
    'COMEDK': {'checked_year': 2026, 'title': 'COMEDK official UGET and counselling information',
        'url': 'https://www.comedk.org/',
        'reason': 'No verified historical marks-to-rank distribution matching this paper is available. College closing ranks are admission cutoffs, not a marks-to-rank conversion.',
        'source_scope': 'Official exam and counselling information; no usable score-to-rank distribution verified.'},
    'BITSAT': {'checked_year': 2026, 'title': 'BITS Pilani official historical admission cutoffs',
        'url': 'https://admissions.bits-pilani.ac.in/FD/BITSAT_cutOffs.html',
        'reason': 'Verified score/merit rank evidence is not available. Published campus/programme cutoff scores cannot determine your national rank; the source maximum and bonus treatment must also match.',
        'source_scope': 'Historical admission cutoffs by programme/year; not candidate rank data.'},
}


DATASETS = {
    'JEE Main': {'year': 2026, 'checked_date': '2026-10-23', 'title': 'Careers360 · JEE Main 2026 marks, percentile and rank analysis',
        'url': 'https://engineering.careers360.com/articles/jee-main-marks-vs-percentile',
        'source_scope': 'Published secondary-source estimates, not an official NTA marks-to-rank distribution. Table checked against the source; predictive accuracy has not been validated.',
        'rows': [
            (291,300,1,15,99.999,100), (280,292,16,56,99.99617561,99.99890732),
            (271,279,86,125,99.99153171,99.99417236), (259,268,142,341,99.97687156,99.99034797),
            (250,258,381,704,99.95228621,99.97413985), (240,249,733,1246,99.91549924,99.95028296),
            (230,239,1269,1909,99.87060821,99.91395128), (220,229,2043,3217,99.78191884,99.86150253),
            (210,219,3319,4549,99.69159044,99.77499852), (200,209,4647,6269,99.57503767,99.68494329),
            (190,199,6488,8724,99.40858575,99.56019541), (180,189,8951,12197,99.17311273,99.39319714),
            (170,179,12439,16524,98.87981861,99.1567225), (160,169,16942,21710,98.52824811,98.85149993),
            (150,159,22156,28132,98.09290531,98.49801724), (140,149,28402,36243,97.54301298,98.07460288),
            (130,139,36985,46047,96.87838902,97.4927496), (120,129,47066,57991,96.0687115,96.80927687),
            (110,119,59254,72925,95.05625037,95.983027), (100,109,74236,91426,93.8020333,94.96737888),
            (90,99,93240,114780,92.21882783,93.67910655), (80,89,117151,143434,90.27631202,92.05811248),
            (70,79,146849,184121,87.51810893,90.0448455), (60,69,186799,237626,83.89085926,87.33654157),
            (50,59,243215,319343,78.35114254,83.5119717), (40,49,327188,448730,69.5797271,77.81927947),
            (30,39,460200,647703,56.09102043,68.80219265),
            (10,19,954561,1207129,18.16647924,35.2885364), (0,9,1222184,1390805,5.71472799,17.14582299),
        ]},
    'COMEDK': {'year': 2025, 'checked_date': '2026-10-23', 'title': 'Physics Wallah · COMEDK 2025 expected rank ranges',
        'url': 'https://www.pw.live/kseab/exams/comedk-uget-marks-vs-rank-2025',
        'source_scope': 'Historical published expectations based on previous trends, not observed official 2025 ranks. Table checked against the source; predictive accuracy has not been validated.',
        'rows': [(170,180,1,10), (160,169,11,50), (150,159,51,150), (140,149,151,350),
                 (130,139,351,800), (120,129,801,1700), (110,119,1701,3200), (100,109,3201,5500),
                 (90,99,5501,9700), (80,89,9701,14000), (70,79,14001,23000), (60,69,23001,36000),
                 (50,59,36001,45000), (40,49,45001,45500), (30,39,45501,48000)]},
}


def compatible_paper(a):
    if not family(a): return False
    if a['exam'] == 'JEE Main':
        from .live_series import valid_paper
        return valid_paper(a) and a['summary']['maximum'] == 300
    if a['exam'] == 'COMEDK':
        r = a['rules']
        counts = Counter(q.get('subject', '').lower().replace('maths', 'mathematics') for q in a['questions'])
        return (a['summary']['maximum'] == 180 and r.get('minutes') == 180
                and counts == Counter({'physics': 60, 'chemistry': 60, 'mathematics': 60})
                and all(q.get('type') == 'mcq' and (q.get('scoring') or r).get('correct') == 1
                        and (q.get('scoring') or r).get('wrong') == 0 for q in a['questions']))
    return False


@router.get('/{id}/historical-rank')
async def historical_rank(id: str, score_version: str = 'original', u=Depends(current)):
    a = await released(id, u)
    if a['exam'] == 'BITSAT':
        from .bitsat_branches import attempt_matches
        return attempt_matches(a, score_version)
    reference = REFERENCES.get(a['exam'])
    dataset = DATASETS.get(a['exam'])
    compatible = score_version == 'original' and compatible_paper(a)
    score = a['summary']['score']
    rows = [row for row in (dataset or {}).get('rows', []) if row[0] <= score <= row[1]] if compatible else []
    reason = (reference or {}).get('reason', 'No verified historical evidence is available for this exam.')
    if not compatible and a['exam'] in DATASETS:
        reason = 'Only original-score full mocks matching the reference exam’s duration, question types, subject counts and marking can be compared. No scaling of chapter tests, retries or corrected scores.'
    elif compatible and not rows:
        reason = 'This score is outside the usable source rows. Gaps and malformed rows are excluded; no interpolation or extrapolation is applied.'
    if dataset:
        reference = {k: v for k, v in dataset.items() if k != 'rows'}
    result = {'state': 'available' if rows else 'unavailable', 'label': 'Approximate historical rank range' if rows else 'Reliable rank estimate unavailable',
              'exam': a['exam'], 'score': score, 'maximum': a['summary']['maximum'], 'rank_low': None, 'rank_high': None,
              'reason': 'Direct lookup of the matching published score band; not your official rank.' if rows else reason,
              'reference': reference, 'evidence_type': 'secondary_published_estimate' if dataset else 'guidance_only_no_rank_mapping',
              'limitation': 'Non-official historical scenario, not a prediction or statistical confidence interval. Shift difficulty, normalization, candidate numbers, best-session rules and tie-breaks can change ranks substantially. Paper difficulty is not calibrated. No AI-generated ranks, marks scaling or invented 2027 data. Platform cohort rank remains separate.'}
    if rows:
        result.update(rank_low=min(r[2] for r in rows), rank_high=max(r[3] for r in rows),
                      score_bands=[{'low': r[0], 'high': r[1]} for r in rows],
                      methodology='Exact published band lookup. Overlapping source rows use the enclosing rank range; source gaps remain unavailable. The ambiguous JEE 20–29 row is excluded.')
        if a['exam'] == 'JEE Main':
            result.update(percentile_low=min(r[4] for r in rows), percentile_high=max(r[5] for r in rows))
    return result
