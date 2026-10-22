"""Evidence gate for real-exam rank context: missing mappings never become invented ranks."""
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


@router.get('/{id}/historical-rank')
async def historical_rank(id: str, score_version: str = 'original', u=Depends(current)):
    a = await released(id, u)
    reference = REFERENCES.get(a['exam'])
    compatible = bool(family(a)) and score_version == 'original'
    reason = (reference or {}).get('reason', 'No verified historical evidence is available for this exam.')
    if not compatible:
        reason = 'This is not a compatible original-score full mock. Chapter tests, incomplete paper formats, corrections, revision retries and competitions cannot be scaled into a real-exam rank.'
    return {'state': 'unavailable', 'label': 'Reliable rank estimate unavailable', 'exam': a['exam'],
            'score': a['summary']['score'], 'maximum': a['summary']['maximum'], 'rank_low': None, 'rank_high': None,
            'reason': reason, 'reference': reference, 'evidence_type': 'guidance_only_no_rank_mapping',
            'limitation': 'A historical same-score scenario is not an official result or a prediction. Platform cohort rank is separate; no marks scaling, invented 2027 data or AI estimates are used.'}
