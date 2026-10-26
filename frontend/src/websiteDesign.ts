import exported from "../assets/website-2026-10-26/design-tokens.json";

// Unmodified owner export, not independently invented colour values.
export const websiteDesign = exported.viewports["390"];
export const websiteMotion = exported.motion;
export type HomeIdentity = "jee-main" | "bitsat" | "comedk" | "all-india";
export const componentStyle = (name: keyof typeof websiteDesign.other_component_states) => websiteDesign.other_component_states[name].style;

export function homeDesign(identity: HomeIdentity) {
  const card = websiteDesign.home_cards[identity];
  const cta = ".exam-primary" in card ? card[".exam-primary"] : card[".flagship-primary"];
  return { card, cta };
}

/** Split CSS gradient layers/stops without splitting rgb()/rgba() commas. */
export function splitCssList(value: string): string[] {
  let depth = 0, start = 0;
  const parts: string[] = [];
  for (let i = 0; i < value.length; i++) {
    if (value[i] === "(") depth++;
    if (value[i] === ")") depth--;
    if (value[i] === "," && depth === 0) { parts.push(value.slice(start, i).trim()); start = i + 1; }
  }
  parts.push(value.slice(start).trim());
  return parts;
}

export function parseGradientLayers(value: string) {
  return splitCssList(value).filter((layer) => layer.startsWith("linear-gradient(")).map((layer) => {
    const stops = splitCssList(layer.slice(16, -1));
    const angle = stops[0].endsWith("deg") ? parseFloat(stops.shift()!) : 180;
    const parsed = stops.map((stop) => {
      const position = stop.match(/\s+([\d.]+)%$/);
      return { color: position ? stop.slice(0, position.index) : stop, offset: position ? Number(position[1]) / 100 : undefined as number | undefined };
    });
    parsed[0].offset ??= 0;
    parsed[parsed.length - 1].offset ??= 1;
    for (let i = 1; i < parsed.length - 1; i++) {
      if (parsed[i].offset !== undefined) continue;
      let next = i + 1;
      while (parsed[next].offset === undefined) next++;
      const previous = parsed[i - 1].offset!;
      const interval = (parsed[next].offset! - previous) / (next - i + 1);
      for (let j = i; j < next; j++) parsed[j].offset = previous + interval * (j - i + 1);
      i = next - 1;
    }
    return { angle, stops: parsed };
  });
}

// CSS magic-corner gradient line: aspect ratio matters (unlike a fixed diagonal).
export function cssGradientLine(angle: number, width: number, height: number) {
  const radians = angle * Math.PI / 180, dx = Math.sin(radians), dy = -Math.cos(radians);
  const length = Math.abs(width * dx) + Math.abs(height * dy);
  return { x1: width / 2 - dx * length / 2, y1: height / 2 - dy * length / 2, x2: width / 2 + dx * length / 2, y2: height / 2 + dy * length / 2 };
}