"""One-off editorial review. NO writes to cards/database; no generation/rewriting.

Every full active JEE source card is independently read by a language model.
Hash-bound decisions persist for resumability. Old keyword/importance cache is NOT used.
Run --limit 1 to validate provider, then without --limit for the full bank.
"""
import argparse
import asyncio
import hashlib
import json
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT = Path(__file__).parent
load_dotenv(ROOT.parent / '.env')
OUT = ROOT / 'portrait_review'
MODEL = 'claude-sonnet-5-5'
SYSTEM = '''You are a rigorous JEE Physics/Chemistry/Mathematics content editor.
REREAD EACH ENTIRE CARD independently: prompt, formula, ALL options, answer index,
explanation, any diagram. Do NOT rewrite or generate any content.
We are curating a 20-second fast-recall game. KEEP only clear scientifically correct
direct concepts, formula recognition, standard relationships, units, trends,
misconceptions or quick diagram interpretation, generally 5-15 seconds for a strong student.
REJECT ANY numerical calculation/substitution (even simple plug-in arithmetic),
pen-and-paper working, solving equations, multi-step derivation, lengthy reading,
borderline timing (approximately 20 seconds OR MORE), ambiguous assumptions/multiple
correct choices/incorrect key, or illegible essential missing diagrams.
Numbers/constants in a direct recall fact, standard angle, or known formula are NOT
automatic rejections. Standard derivative/primitive RECOGNITION can be direct recall;
performing a calculation, equation solving or algebraic manipulation is NOT.
Judge the mental work actually required, not keywords. Never keep a borderline card
to meet a count. A question about a conceptual proportionality is fine without numerical evaluation.
Return ONLY one JSON array containing exactly one object for each input id, in order:
{"id":"...","keep":true/false,"estimated_seconds":integer,"reason_code":"recall|calculation|multistep|lengthy|borderline|ambiguous|incorrect|missing_diagram","reason":"brief card-specific rationale, 8-22 words"}.
Estimate reading + recognizing + answering, not just calculation. For KEEP use reason_code=recall
and estimated_seconds <=15. For rejected cards choose the primary reason. Answer indices are zero based.
Do not include the original question or answer in your rationale. No markdown.'''


def digest(card):
    return hashlib.sha256(json.dumps(card, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def source_cards():
    return [(p, c) for p in sorted((ROOT / 'cards').glob('*.json'))
            if not p.name.startswith('biology') for c in json.loads(p.read_text())
            if c['subject'] in ('Physics', 'Chemistry', 'Mathematics')]


async def review(batch, sem):
    key = hashlib.sha256(''.join(digest(c) for _, c in batch).encode()).hexdigest()
    dest = OUT / (key + '.json')
    if dest.exists():
        return
    async with sem:
        chat = LlmChat(api_key=os.environ['EMERGENT_LLM_KEY'], session_id='rf-review-' + uuid.uuid4().hex,
                       system_message=SYSTEM).with_model('anthropic', MODEL).with_params(max_tokens=6500)
        # Explicit non-streaming offline editorial artifact, never a user-facing chat response.
        # Small transport IDs avoid long UUID transcription; ALL scientific content stays intact.
        listing = [{**c, 'id': str(i)} for i, (_, c) in enumerate(batch)]
        text = await chat.send_message(UserMessage(text=json.dumps(listing, ensure_ascii=False)))
        start = text.find('[')
        if start < 0:
            raise ValueError('Review omitted JSON')
        rows = json.JSONDecoder().raw_decode(text[start:])[0]
        if len(rows) != len(batch) or [str(r.get('id')) for r in rows] != [str(i) for i in range(len(batch))]:
            Path('/tmp/rf-invalid-review.txt').write_text(text)
            raise ValueError('Incomplete/incorrect review IDs; nothing applied')
        for row, (path, card) in zip(rows, batch):
            assert isinstance(row['keep'], bool), 'Non-boolean decision'
            assert isinstance(row['estimated_seconds'], int) and row['estimated_seconds'] > 0, 'Invalid timing estimate'
            assert row['reason_code'] in ('recall', 'calculation', 'multistep', 'lengthy', 'borderline', 'ambiguous', 'incorrect', 'missing_diagram'), 'Invalid reason code: ' + str(row['reason_code'])
            assert isinstance(row['reason'], str) and len(row['reason']) > 12, 'Missing rationale'
            if row['keep'] and row['estimated_seconds'] > 15:
                row.update(keep=False, reason_code='borderline', reason='Reviewer timing estimate exceeds the conservative 15-second active-pool limit.')
            assert not row['keep'] or row['reason_code'] == 'recall', 'Contradictory keep/reason verdict'
            row.update(id=card['id'], sha256=digest(card), file=path.name, subject=card['subject'], chapter=card['chapter'], model=MODEL)
        dest.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
        print('REVIEWED', len(rows), 'kept', sum(r['keep'] for r in rows), key[:10], flush=True)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    cards = source_cards()
    batches = [cards[i:i+30] for i in range(0, len(cards), 30)]
    print('BANK', len(cards), 'BATCHES', len(batches), 'MODEL', MODEL, flush=True)
    sem = asyncio.Semaphore(6)
    outcomes = await asyncio.gather(*(review(b, sem) for b in batches[:args.limit]), return_exceptions=True)
    failures = [type(e).__name__ + ': ' + str(e)[:140] for e in outcomes if isinstance(e, Exception)]
    print('FINISHED failed_batches=', len(failures), failures[:3], flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(main())