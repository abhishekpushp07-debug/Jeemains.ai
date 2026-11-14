import { Image } from "expo-image";
import { RF_BASE } from "@/src/api/client";

// Cheer squad sprites: four poses per dancer. Level 1 ships inside the app; levels 2-4 download from the server the
// first time they are needed (then stay in the image cache), so they never add to the app size.
// `grip`: where each holder pose holds the banner pole (share of the sprite width / height), measured from the art.
export type Who = "a" | "b" | "c";
type Geo = { a: { aspect: number; grip: number[][] }; b: { aspect: number; grip: number[][] }; c: { aspect: number } };
export const SQUAD_GEO: Record<number, Geo> = {"1": {"a": {"aspect": 0.6422, "grip": [[0.8477, 0.0364], [0.8495, 0.0466], [0.8474, 0.0468], [0.8485, 0.1518]]}, "b": {"aspect": 0.823, "grip": [[0.7214, 0.0352], [0.7219, 0.0465], [0.7211, 0.0456], [0.7214, 0.2286]]}, "c": {"aspect": 0.7571}}, "2": {"a": {"aspect": 0.6438, "grip": [[0.8455, 0.0358], [0.8463, 0.0452], [0.8471, 0.0463], [0.846, 0.1501]]}, "b": {"aspect": 0.8245, "grip": [[0.7216, 0.0351], [0.7204, 0.0455], [0.7206, 0.0456], [0.7207, 0.2295]]}, "c": {"aspect": 0.7606}}, "3": {"a": {"aspect": 0.6406, "grip": [[0.8521, 0.0359], [0.8521, 0.0494], [0.8532, 0.0472], [0.8526, 0.1535]]}, "b": {"aspect": 0.8288, "grip": [[0.7173, 0.0338], [0.7189, 0.0425], [0.7174, 0.0436], [0.7182, 0.2281]]}, "c": {"aspect": 0.7592}}, "4": {"a": {"aspect": 0.6422, "grip": [[0.8473, 0.0354], [0.8452, 0.0458], [0.8468, 0.0468], [0.8463, 0.1504]]}, "b": {"aspect": 0.8245, "grip": [[0.7199, 0.0353], [0.7203, 0.0449], [0.7203, 0.0455], [0.7206, 0.2294]]}, "c": {"aspect": 0.7592}}};

const LOCAL: Record<Who, number[]> = {
  a: [require("../../assets/squad/squad1_a1.webp"), require("../../assets/squad/squad1_a2.webp"), require("../../assets/squad/squad1_a3.webp"), require("../../assets/squad/squad1_a4.webp")],
  b: [require("../../assets/squad/squad1_b1.webp"), require("../../assets/squad/squad1_b2.webp"), require("../../assets/squad/squad1_b3.webp"), require("../../assets/squad/squad1_b4.webp")],
  c: [require("../../assets/squad/squad1_c1.webp"), require("../../assets/squad/squad1_c2.webp"), require("../../assets/squad/squad1_c3.webp"), require("../../assets/squad/squad1_c4.webp")],
};

export const squadFrames = (level: number, who: Who): (number | { uri: string })[] =>
  level <= 1 || !SQUAD_GEO[level] ? LOCAL[who] : [1, 2, 3, 4].map((i) => ({ uri: `${RF_BASE}/art/squad${level}_${who}${i}.webp` }));

/** Start downloading a squad level before the show opens, so every pose is ready on the first beat. */
export const prefetchSquad = (level?: number) => {
  if (!level || level <= 1) return;
  Image.prefetch((["a", "b", "c"] as Who[]).flatMap((w) => squadFrames(level, w).map((f) => (f as { uri: string }).uri))).catch(() => {});
};
