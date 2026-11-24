// The owner's website export (assets/website-2026-10-26/design-tokens.json, unmodified) is the source of these colours;
// none is invented here. Only the values the app reads are copied, word for word, from
// viewports["390"].other_component_states[<name>].style, so the 95 KB export is not carried inside the app and read at
// every start. `python3 /app/tests/tools/website_tokens.py` checks that each value below still equals the export.
const STYLES = {
  "library.completed": { borderTopColor: "rgb(86, 217, 154)" },
  "library.saved": { borderTopColor: "rgb(255, 105, 116)" },
  "library.active": { borderTopColor: "rgb(217, 119, 6)" },
} as const;
export const componentStyle = (name: keyof typeof STYLES) => STYLES[name];
