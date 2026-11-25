// A Matched question for the phone's typesetter: its words and its options as one piece of HTML, so a question with
// maths costs one typesetter, not one per option. Plain strings in, a string out (no React here), so it can be checked
// in a browser without the app.
export const LETTERS = "ABCDEF";
type Tex = (text: string) => string;
export type SidePalette = { ink: string; soft: string; line: string; ring: string; green: string; greenInk: string; greenLine: string; wash: string; onGreen: string; red: string; redWash: string };

export const stemHtml = (text: string, tex: Tex) => (text ? `<div class="stem">${tex(text)}</div>` : "");

/** `right` = the place of the right option once the solution is open (it is drawn green, with a tick); null before that.
 *  `wrong` = the place of the option the student chose in the paper when it was not the right one (red, with a cross). */
export const optionsHtml = (options: string[], right: number | null, wrong: number | null, tex: Tex) => options.map((o, i) =>
  `<div class="opt${i === right ? " right" : i === wrong ? " wrong" : ""}"><span class="l">${LETTERS[i]}</span><span class="t">${tex(o)}</span>${i === right ? '<span class="ok">&#10003;</span>' : i === wrong ? '<span class="no">&#10005;</span>' : ""}</div>`).join("");

/** The same rows as the plain ones in QuestionBlock.tsx: a round letter, the option, a hairline frame; green when right. */
export const sideCss = (c: SidePalette) => `body{margin:0;background:transparent;color:${c.ink};font:15px -apple-system,Roboto,sans-serif;line-height:1.55;overflow-wrap:anywhere}`
  + `.stem,.t{white-space:pre-wrap}.t{flex:1;min-width:0}`
  + `.opt{display:flex;align-items:center;gap:12px;margin-top:8px;padding:8px 12px;border-radius:14px;border:1.5px solid ${c.line}}.opt:first-child{margin-top:0}.stem+.opt{margin-top:12px}`
  + `.l{flex:0 0 26px;height:26px;box-sizing:border-box;border-radius:13px;border:1.5px solid ${c.ring};display:flex;align-items:center;justify-content:center;font-weight:800;font-size:12px;line-height:1;color:${c.soft}}`
  + `.right{border-color:${c.greenLine};background:${c.wash}}.right .l{background:${c.green};border-color:${c.green};color:${c.onGreen}}.ok{font-weight:800;color:${c.greenInk}}`
  + `.wrong{border-color:${c.red};background:${c.redWash}}.wrong .l{background:${c.red};border-color:${c.red};color:${c.onGreen}}.no{font-weight:800;color:${c.red}}`
  + `.katex-display{overflow-x:auto;overflow-y:hidden;margin:6px 0}.katex{font-size:1.05em}`;
