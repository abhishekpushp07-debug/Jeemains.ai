// The website cuts a typeset question into pieces: the question itself ("q", one or more) and one piece per option.
// Every piece is a tight picture sized in print points (w × h); the picture file holds 2 pixels per point.
export type Piece = { part: string; w: number; h: number };
export const piecesOf = (q?: { pieces?: Piece[] | null } | null): Piece[] | null => (Array.isArray(q?.pieces) && q.pieces.length ? q.pieces : null);

// Owner's rule: a PYQ paper keeps its original look - the whole question picture with the number buttons under it,
// no content inside the options - even when the website also sends cut pieces for it. Mocks, chapter-wise tests and
// the All India series get the cut look. The pieces of a PYQ paper are dropped the moment the paper arrives, so no
// screen, image grant or paper pack ever sees them.
type Paper = { test_kind?: string | null; set_id?: string | null; questions?: any[] | null };
export const isPyq = (paper?: Paper | null) => paper?.test_kind === "pyq" || /(^|-)pyq-/.test(String(paper?.set_id ?? ""));
export function originalLook<T extends Paper | null | undefined>(paper: T): T {
  if (isPyq(paper) && Array.isArray(paper!.questions)) for (const q of paper!.questions) if (q?.pieces) q.pieces = null;
  return paper;
}

// Steps of the text-size button for cut questions (the website's steps).
export const PIECE_ZOOM = [1, 1.35, 1.8];
// Room the frames take around the pictures. components/Pieces.tsx draws its frames from these same numbers.
export const FRAME = { stemPad: 14, stemLine: 1, cardPad: 10, cardLine: 2, chip: 34, tick: 26, gap: 10, paperPad: 12, paperLine: 1 };
const STEM_FRAME = 2 * (FRAME.stemPad + FRAME.stemLine);
const PAPER_FRAME = 2 * (FRAME.cardPad + FRAME.cardLine + FRAME.paperPad + FRAME.paperLine); // an option's paper spanning its whole card
const OPTION_FRAME = PAPER_FRAME + 2 * FRAME.gap + FRAME.chip + FRAME.tick; // ... and beside its letter and its tick
const LARGEST = 1.5; // a short question on a wide screen is never blown up past 1.5x its printed size
const PRINTED = 1; // on a phone a wide question has to shrink to fit; its options still come at the printed size

/** Scale of the question pictures and of the option pictures in a column `width` wide.
 *  Without zoom everything fits: the question its paper, every option its card. Zoom enlarges both alike;
 *  a picture that no longer fits scrolls sideways inside its paper.
 *  `stack`: long options that would have to shrink below their printed size beside the letter get the whole card
 *  width instead (the letter and the tick move above the paper), so on a phone they stay as large as they can be. */
export function pieceLayout(pieces: Piece[], typed: Record<string, string> | null | undefined, width: number, zoom = 1) {
  const widest = (own: (p: Piece) => boolean) => Math.max(0, ...pieces.filter(own).map(p => p.w));
  const stemWide = Math.max(1, widest(p => p.part === "q")), optionWide = widest(p => p.part !== "q" && !typed?.[p.part]);
  const fit = Math.min(LARGEST, Math.max(1, width - STEM_FRAME) / stemWide);
  const beside = optionWide ? Math.max(1, width - OPTION_FRAME) / optionWide : Infinity;
  const stack = beside < PRINTED;
  const room = stack ? Math.max(1, width - PAPER_FRAME) / optionWide : beside;
  return { stem: fit * zoom, option: Math.min(Math.max(fit, PRINTED), room) * zoom, stack };
}
