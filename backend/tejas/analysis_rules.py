"""Analysis rulebook v1: one set of definitions for the website, the app and the PDF. Change a number here and raise VERSION."""

VERSION = 2
RULES = {
    'version': VERSION,
    'stretch_cap': 900,  # one on-screen stretch counts for at most 15 minutes
    'par': {'min_solvers': 30, 'floor': 30, 'ceiling_x_average': 2, 'type_factor': {'mcq': 0.85, 'integer': 1.35}, 'share_of_duration': 0.9},
    'quality': {'perfect_x': 1.25, 'wasted_x': 0.5, 'gap_x': 1.5, 'confused_x': 0.5},
    'difficulty': {'min_attempted': 50, 'early_attempted': 10, 'easy': 65, 'tough': 35},
    'extra': {'lucky_x': 0.25, 'last_share': 0.2, 'last_min': 5},
    'potential': {'guard_solved_below': 25},
    'compare': {'min_finishers': 10},
    'block': {'long': 1800, 'short': 900, 'short_upto_minutes': 60, 'most': 12},
}
TAGS = ('perfect', 'slow_correct', 'wasted', 'concept_gap', 'costly_overtime', 'confused', 'smart_skip', 'not_seen', 'no_score')
LEVELS = ('easy', 'moderate', 'tough', 'unrated')
COPY = {
    'tags': {
        'perfect': ['Perfect', 'Sahi jawab, sahi time mein.'],
        'slow_correct': ['Slow-correct', 'Jawab sahi, lekin Par time se zyada laga.'],
        'wasted': ['Careless galti', 'Bahut jaldi mein galat. Ek baar dobara padhte to bach jaata.'],
        'concept_gap': ['Concept gap', 'Poora time diya, phir bhi galat. Concept dobara dekho.'],
        'costly_overtime': ['Mehnga overtime', 'Bahut zyada time laga aur jawab bhi galat.'],
        'confused': ['Confused', 'Time lagaya, lekin jawab nahi diya.'],
        'smart_skip': ['Smart skip', 'Dekha aur jaldi chhod diya. Time bacha.'],
        'not_seen': ['Dekha hi nahi', 'Yeh sawaal khula hi nahi.'],
        'no_score': ['Score se bahar', 'Dropped ya sabko bonus mila: tag nahi lagta.'],
    },
    'levels': {'easy': 'Easy', 'moderate': 'Moderate', 'tough': 'Tough', 'unrated': 'Not rated'},
    'time_label': 'Time = sawaal screen par kitni der khula raha (time on screen).',
    'level_sources': {'students': 'students ke result se', 'early': 'shuruaati result se', 'paper': 'paper ke tag se', 'none': 'abhi Not rated'},
}
_LEVEL = {'easy': 'easy', 'moderate': 'moderate', 'medium': 'moderate', 'hard': 'tough', 'tough': 'tough', 'difficult': 'tough'}


def standard_par(questions, minutes, rules=RULES):
    """Paper standard: the paper's time shared by question type, adding up to 90% of its duration."""
    if not minutes or not questions:
        return {}
    factor = rules['par']['type_factor']
    weight = {q['id']: factor.get(q['type'], 1) for q in questions}
    total = sum(weight.values())
    return {qid: round(rules['par']['share_of_duration'] * minutes * 60 * w / total, 1) for qid, w in weight.items()}


def par_for(q, standard, stat, average, rules=RULES):
    """(seconds or None, where it came from, number of solvers behind it)."""
    p = rules['par']
    if stat and stat.get('solvers', 0) >= p['min_solvers'] and stat.get('median') is not None:
        top = max(p['floor'], p['ceiling_x_average'] * average) if average else stat['median']
        return max(p['floor'], min(stat['median'], top)), 'solvers', stat['solvers']
    if q['id'] in standard:
        return standard[q['id']], 'standard', 0
    return None, 'none', 0


def tag_for(outcome, seconds, par, seen, rules=RULES):
    """Exactly one tag per question, or None when its time was not recorded."""
    k = rules['quality']
    if outcome in ('dropped', 'bonus'):
        return 'no_score'
    if seconds is None:
        return None
    if outcome == 'skipped':
        if not seen and not seconds:
            return 'not_seen'
        return 'confused' if par and seconds > k['confused_x'] * par else 'smart_skip'
    if not par:
        return None
    if outcome == 'correct':
        return 'perfect' if seconds <= k['perfect_x'] * par else 'slow_correct'
    if seconds < k['wasted_x'] * par:
        return 'wasted'
    return 'concept_gap' if seconds <= k['gap_x'] * par else 'costly_overtime'


def difficulty_for(q, stat, hint=None, rules=RULES):
    """(level, source): student results first, then the paper's own tag, otherwise not rated. Never guessed."""
    d = rules['difficulty']
    if stat and stat.get('attempted', 0) >= d['min_attempted']:
        share = 100 * stat['correct'] / stat['attempted']
        return ('easy' if share >= d['easy'] else 'tough' if share < d['tough'] else 'moderate'), 'students'
    level = _LEVEL.get(str(q.get('difficulty') or hint or '').strip().lower())
    if level:
        return level, 'paper'
    # Fewer students so far: an early level, always labelled as early.
    if stat and stat.get('attempted', 0) >= d['early_attempted']:
        share = 100 * stat['correct'] / stat['attempted']
        return ('easy' if share >= d['easy'] else 'tough' if share < d['tough'] else 'moderate'), 'early'
    return 'unrated', 'none'
