// Design tokens for JEELIVE.AI. Keys match the "color" block of /app/design_guidelines.json.
import { createContext, useContext, useMemo } from "react";
import { Appearance, Platform, StyleSheet, ViewStyle, TextStyle, ImageStyle } from "react-native";
import { componentStyle } from "./websiteDesign";

export type ColorScheme = "light" | "dark";

// Previous dark luxury palette — kept only as the base of the isolated Rapid Fire identity.
const dark = {
  surface: "#08080A",
  onSurface: "#F8FAFC",
  surfaceSecondary: "#14141C",
  onSurfaceSecondary: "#F8FAFC",
  surfaceAlt: "#0F0F14",
  surfaceTertiary: "#280D13",
  onSurfaceTertiary: "#FF6974",
  surfaceInverse: "#D91222",
  onSurfaceInverse: "#FFFFFF",
  muted: "#B0B0BF",
  mutedSecondary: "#9292A5",
  brandText: "#FF6974", // live jeelive.ai text/icon red, distinct from button fill
  brandLine: "#67202C",
  focusRing: "#FF7883",

  brand: "#D91222",
  onBrand: "#FFFFFF",
  brandPrimary: "#D91222",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#B91020",
  onBrandSecondary: "#FFFFFF",
  brandTertiary: "#280D13",
  onBrandTertiary: "#FF6974",

  success: "#56D99A",
  onSuccess: "#10231C",
  warning: "#F1BC63",
  onWarning: "#2A2113",
  error: "#FF7883",
  onError: "#2F1118",
  info: "#FF6974",
  onInfo: "#280D13",

  border: "#2A2A38",
  borderStrong: "#454557",
  divider: "#2A2A38",

  // Legacy exam/brand aliases remain stable for existing screens and game UI.
  custom_examJee: "#D91222",
  custom_examJeeDeep: "#280D13",
  custom_examBitsat: "#D91222",
  custom_examBitsatDeep: "#280D13",
  custom_examComedk: "#14141C",
  custom_examComedkGold: "#FF6974",
  custom_series: "#160B10",
  custom_seriesBright: "#FF7883",
  custom_burgundy: "#67202C",
  custom_subjectPhysics: "#FF6974",
  custom_subjectChemistry: "#F1BC63",
  custom_subjectMaths: "#5EEAD4",
  custom_subjectBiology: "#56D99A",
  custom_darkCard: "#14141C",
  custom_amber: "#906224",
  custom_cyan: "#FF6974",
  custom_reading: "#14141C",
  custom_onReading: "#F8FAFC",
  custom_successSoft: "#10231C",
  custom_errorSoft: "#2F1118",
  custom_warningSoft: "#2A2113",
  custom_infoSoft: "#280D13",
  custom_gameBg: "#08080A",
  custom_gameCard: "#14141C",
  custom_gameCardHi: "#1A1A24",
  custom_gameLine: "#2A2A38",
  custom_neonAmber: "#F1BC63",
  custom_neonCyan: "#FF6974",
  custom_neonGreen: "#56D99A",
  custom_neonViolet: "#5EEAD4",
  custom_neonMagenta: "#FF6974",
  custom_rarityRare: "#C0C6CF",
  custom_rarityEpic: "#2DD4BF",
  custom_rarityLegendary: "#F1BC63",
  custom_rarityCommon: "#B0B0BF",
  custom_neonRed: "#FF7883",
  custom_gameMuted: "#B0B0BF",
  custom_overlay: "rgba(8,8,10,0.85)",
  custom_whiteA70: "rgba(248,250,252,0.72)",
  custom_whiteA15: "rgba(248,250,252,0.15)",

  // Exact academic-card colours from the owner's learning-workspace.css handoff.
  // Scoped tokens: changing these must not recolour Rapid Fire.
  custom_webJeeBackground: "#B00000",
  custom_webJeeAccent: "#FFE4E4",
  custom_webJeeMuted: "#FFEAEA",
  custom_webJeeLine: "#FF9494A0",
  custom_webJeeButtonInk: "#8A0000",
  custom_webBitsatBackground: "#FF9933",
  custom_webBitsatInk: "#2B1600",
  custom_webBitsatAccent: "#542600",
  custom_webBitsatMuted: "#4A230B",
  custom_webBitsatLine: "#9E4D1770",
  custom_webBitsatButton: "#3D1D0A",
  custom_webBitsatButtonInk: "#FFF7ED",
  custom_webComedkBackground: "#101115",
  custom_webComedkAccent: "#E5D5AF",
  custom_webComedkMuted: "#CDD0DA",
  custom_webComedkLine: "#DDE3EE40",
  custom_webComedkButton: "#ECEEF2",
  custom_webWhite: "#FFFFFF",
  custom_webGlass: "#FFFFFF09",
  custom_webGlassLine: "#FFFFFF1A",
  custom_webFinishStrong: "#FFFFFF20",
  custom_webFinishSoft: "#FFFFFF05",
  custom_webJeeFinish: "#FFFFFF08",
  custom_webJeeShine: "#FFFFFF40",
  custom_webBitsatShine: "#FFFFFF78",
  custom_webTransparent: "#FFFFFF00",
  custom_webShadowClear: "#00000000",
  custom_webBottomShade: "#0000000A",
  custom_webExamShadow: "#0C1835",
  custom_webLearningMaroon: "#5C0025",
  custom_webLearningCompleted: "#0284C7",
  custom_webLearningSaved: "#2563EB",
  custom_webLearningActive: "#D97706",
  custom_webLearningError: "#DC2626",
  custom_webMaroonSoft: "#FDF2F5",
  custom_webCompletedSoft: "#F0F9FF",
  custom_webCompletedInk: "#075985",
  custom_webSavedSoft: "#EFF6FF",
  custom_webSavedInk: "#1E40AF",
  custom_webActiveSoft: "#FFFBEB",
  custom_webActiveInk: "#92400E",
  custom_webErrorSoft: "#FEF2F2",
  custom_webErrorInk: "#991B1B",

  // 2026 design language: calm dark surfaces, thin lines, All India status pastels.
  custom_card: "#111117",
  custom_cardRaised: "#16161E",
  custom_cardLine: "#26262F",
  custom_cardLineStrong: "#2E2E38",
  custom_bar: "#0B0B0E",
  custom_barLine: "#1E1E26",
  custom_eyebrow: "#8A8A99",
  custom_dim: "#6E6E7A",
  custom_softText: "#D6D6E0",
  custom_pastelInk: "#1A1A22",
  custom_selectedOption: "#1C0D11",
  custom_todayFrom: "#FFDDBF", custom_todayTo: "#FFB9CC", custom_todayInk: "#8A3350", custom_todayBody: "#5B4048", custom_todayCta: "#FFE3D6",
  custom_doneFrom: "#DDF5C8", custom_doneTo: "#BCE8A2", custom_doneInk: "#3A6B1F", custom_doneBody: "#44603A", custom_doneCta: "#DDF5C8",
  custom_upFrom: "#C7F2EC", custom_upTo: "#8FDDD3", custom_upInk: "#0F5F58", custom_upBody: "#2C5753", custom_upCta: "#D2F6F1",
  custom_missFrom: "#F3E7D8", custom_missTo: "#ECD6DC", custom_missInk: "#7A4A3C", custom_missBody: "#5E4A44", custom_missCta: "#F3E7D8",
  custom_qAnswered: "#22C55E", custom_qNotAnswered: "#EF4444", custom_qMarked: "#0D9488", custom_qMarkedInk: "#5EEAD4",
  custom_qMarkedSoft: "#0B2A27", custom_qFresh: "#2A2A33", custom_qFreshLine: "#3A3A46", custom_qInk: "#FFFFFF",
  custom_gold: "#FFC94D", custom_goldDeep: "#5A3B00", custom_flame: "#FF8A3D", custom_flameSoft: "#2A160C",
  custom_goldSoft: "#2A2410", custom_missSoft: "#2A1A20",
  custom_timerAmber: "#FFB547", custom_savedBlue: "#9DB8FF", custom_mint: "#3DDC97", custom_mintSoft: "#10261A",
  custom_comedkGlow: "#8A90A6", custom_bitsatGlow: "#FF9933", custom_jeeGlow: "#B00000",
  custom_diamondFrom: "#FF4A5A", custom_diamondTo: "#A3000E",
  custom_shade: "rgba(0,0,0,0.62)",
  // Ink-black dock, promo and chip tints shared by both palettes.
  custom_dock: "#0B0B0D", custom_dockInk: "#FFFFFF", custom_dockMuted: "#7C7C85", custom_dockOrb: "#141417", custom_dockOrbLine: "#2C2C32",
  custom_promoFrom: "#E6F7F3", custom_promoTo: "#F1F6FF", custom_promoInk: "#0F766E",
  custom_chipFrom: "#FFFFFF", custom_chipTo: "#F3F3F6",
  // All India card: onyx → deep ruby with a soft red glow and a hairline sheen.
  custom_seriesFrom: "#0B0B0D", custom_seriesMid: "#17090D", custom_seriesTo: "#3A0912", custom_seriesGlow: "#E11D2E",
  custom_seriesSheen: "rgba(255,255,255,0.24)", custom_clear: "rgba(255,255,255,0)",
  // Matte royal maroon for exam names; light royal blue that matches the Rapid Fire diamond.
  custom_royalMaroon: "#7A1F35", custom_gemBlue: "#8FA8FF",
};

export type ThemeColors = typeof dark;

// 2026 "quiet light" academic palette: white canvas, near-black ink, hairline borders,
// red only as a small brand accent, black primary actions.
const light: ThemeColors = {
  ...dark,
  surface: "#FFFFFF", onSurface: "#0F0F12",
  surfaceSecondary: "#FFFFFF", onSurfaceSecondary: "#0F0F12",
  surfaceAlt: "#F6F6F8",
  surfaceTertiary: "#FFF1F2", onSurfaceTertiary: "#C1121F",
  surfaceInverse: "#0F0F12", onSurfaceInverse: "#FFFFFF",
  muted: "#6B6B75", mutedSecondary: "#8C8C96",
  brandText: "#C1121F", brandLine: "#F5C9CE", focusRing: "#D91222",
  brand: "#D91222", onBrand: "#FFFFFF", brandPrimary: "#D91222", onBrandPrimary: "#FFFFFF",
  brandSecondary: "#A50E1B", onBrandSecondary: "#FFFFFF",
  brandTertiary: "#FFF1F2", onBrandTertiary: "#C1121F",
  success: "#15803D", onSuccess: "#FFFFFF", warning: "#B45309", onWarning: "#FFFFFF",
  error: "#DC2626", onError: "#FFFFFF", info: "#3C3C44", onInfo: "#FFFFFF",
  border: "#E8E8EC", borderStrong: "#D4D4DA", divider: "#EFEFF2",

  custom_examJee: "#D91222", custom_examJeeDeep: "#FFF1F2", custom_examBitsat: "#D97706", custom_examBitsatDeep: "#FFF6E8",
  custom_examComedk: "#3C3C44", custom_examComedkGold: "#A27B2C",
  custom_series: "#0E0E10", custom_seriesBright: "#FF5A66", custom_burgundy: "#8A1C2B",
  custom_subjectPhysics: "#D9363E", custom_subjectChemistry: "#C27C0E", custom_subjectMaths: "#0D9488", custom_subjectBiology: "#15803D",
  custom_darkCard: "#F6F6F8", custom_amber: "#B45309", custom_cyan: "#C1121F",
  custom_reading: "#FFFFFF", custom_onReading: "#1A1A1F",
  custom_successSoft: "#EAF7EE", custom_errorSoft: "#FEF2F2", custom_warningSoft: "#FFF7E6", custom_infoSoft: "#F4F4F7",
  custom_gameBg: "#FFFFFF", custom_gameCard: "#FFFFFF", custom_gameCardHi: "#F6F6F8", custom_gameLine: "#ECECF0",
  custom_neonAmber: "#B45309", custom_neonCyan: "#0F766E", custom_neonGreen: "#15803D", custom_neonViolet: "#0D9488", custom_neonMagenta: "#C1121F",
  custom_rarityRare: "#6B7280", custom_rarityEpic: "#0D9488", custom_rarityLegendary: "#B7791F", custom_rarityCommon: "#8E8E97",
  custom_neonRed: "#DC2626", custom_gameMuted: "#6B6B75",
  custom_overlay: "rgba(15,15,18,0.55)",

  custom_card: "#FFFFFF", custom_cardRaised: "#F6F6F8", custom_cardLine: "#ECECF0", custom_cardLineStrong: "#DEDEE4",
  custom_bar: "#F6F6F8", custom_barLine: "#ECECF0",
  custom_eyebrow: "#74747E", custom_dim: "#A6A6AE", custom_softText: "#3C3C44", custom_pastelInk: "#111114",
  custom_selectedOption: "#FFF4F5",
  custom_qAnswered: "#16A34A", custom_qNotAnswered: "#DC2626", custom_qMarked: "#0D9488", custom_qMarkedInk: "#0F766E",
  custom_qMarkedSoft: "#E6F6F4", custom_qFresh: "#F1F1F4", custom_qFreshLine: "#D9D9DF", custom_qInk: "#FFFFFF",
  custom_gold: "#B7791F", custom_goldDeep: "#7A4E00", custom_flame: "#EA580C", custom_flameSoft: "#FFF0E6",
  custom_goldSoft: "#FFF6DB", custom_missSoft: "#FBEFF1",
  custom_timerAmber: "#B45309", custom_savedBlue: "#2563EB", custom_mint: "#15803D", custom_mintSoft: "#EAF7EE",
  custom_jeeGlow: "#D91222",
  custom_shade: "rgba(15,15,18,0.45)",
};

export const defaultScheme = "light" satisfies ColorScheme;
Appearance.setColorScheme?.(defaultScheme); // academic screens are always the light palette

export const colors = light;

// Rapid Fire is its own world: the Blood Red Arena. Academic tokens above never recolour it.
// Shining blood red is the stage, teal is only for things you press, gold is only for wins, rewards and special frames.
export const arena = {
  bgTop: "#B0101E", bg: "#7C0913", bgDeep: "#45050C", mark: "#C2283A", vignette: "#140103", glow: "#FF3B4E",
  // Cards and player rows are near-black cherry glass with a ruby rim, so they stand clear of the blood-red stage.
  panel: "#16070A", panelHi: "#2B0C12", panelEdge: "#0A0304", rim: "#8E2231", rimHi: "#FF6B7A", bar: "#0D0406",
  teal: "#14B8A6", tealHi: "#3EE6D0", tealDeep: "#0B6F65", tealOutline: "#064E47",
  gold: "#FFD75E", goldDeep: "#C98A12", goldSoft: "rgba(255,215,94,0.16)",
  aqua: "#9EF3E6", text: "#FFFFFF", muted: "#EBBFC6", faint: "#C9929C",
  badge: "#FFE14D", badgeInk: "#3A0610", online: "#3DDC84", danger: "#FFB4B4", black: "#000000",
  clear: "rgba(255,255,255,0)", sheen: "rgba(255,255,255,0.5)", gloss: "rgba(255,255,255,0.26)", shade: "rgba(0,0,0,0.45)", scrim: "rgba(20,2,6,0.86)",
  // The shine: a band of light that crosses the stage, and the glassy top of every card.
  shine: "rgba(255,255,255,0.12)", panelGloss: "rgba(255,255,255,0.08)", glint: "rgba(255,255,255,0.78)",
};
// The five streak diamonds, and the lights used by entry effects.
export const gemColors = { red: "#FF4D5E", blue: "#4D7CFF", emerald: "#2FD27A", gold: "#FFD75E", kohinoor: "#F4F8FF" };
export const fx = { fire: "#FF7A2F", ember: "#FFC24D", bolt: "#7DF9FF", white: "#FFFFFF", smoke: "#C9CED6", gold: "#FFD75E", crimson: "#FF4D5E", sky: "#4D7CFF", ice: "#9EF3E6", night: "#0B1026" };
// The stadium banner the Cheer Squad carries, per squad level: satin cloth (top → bottom), metallic foil for the letters,
// the trim on the border, poles and fringe (light → deep), the corner stripes, the letter outline, the name plate and the glitter.
const goldFoil = ["#FFF8D6", "#FFD75E", "#B8760C", "#FFE38A", "#FFF8D6"] as const, goldTrim = ["#FFF2B8", "#E2A82A", "#8A5806"] as const;
export const cheer = {
  1: { cloth: ["#E3203A", "#9A0B1D", "#4A030B"], foil: goldFoil, trim: goldTrim, stripe: "#FFD75E", ink: "#3A0610", plate: "#1A0307", glitter: ["#FFFFFF", "#FFE89A"] },
  2: { cloth: ["#3A2C14", "#140D04", "#000000"], foil: goldFoil, trim: goldTrim, stripe: "#FFD75E", ink: "#1A1204", plate: "#000000", glitter: ["#FFFFFF", "#FFD75E"] },
  3: { cloth: ["#3557E6", "#152686", "#060B36"], foil: ["#FFFFFF", "#E3EBF7", "#8794AC", "#F4F7FF", "#FFFFFF"], trim: ["#FFFFFF", "#B4BED0", "#5A6579"], stripe: "#DCE6F5", ink: "#050A2A", plate: "#040822", glitter: ["#FFFFFF", "#9EC3FF"] },
  4: { cloth: ["#5A1E3A", "#2A0A1E", "#0E0209"], foil: ["#FFF1EA", "#F4B9A4", "#B76E5D", "#FFD9CC", "#FFF1EA"], trim: ["#FFE7DC", "#D99682", "#87483B"], stripe: "#F4B9A4", ink: "#22051A", plate: "#160410", glitter: ["#FFFFFF", "#FFD1E8", "#9EF3E6"] },
} as const;

export const rapidColors = {
  ...dark,
  surface: "#100508", surfaceSecondary: "#1F0A0E", surfaceAlt: "#160709",
  surfaceTertiary: arena.panelHi, onSurfaceTertiary: arena.aqua,
  surfaceInverse: "#2A0509", onSurface: arena.text, onSurfaceInverse: arena.text, onSurfaceSecondary: arena.muted,
  brand: arena.teal, brandPrimary: arena.teal, brandText: arena.aqua, brandLine: arena.tealDeep, brandSecondary: "#0E8F81",
  brandTertiary: "#0E3A36", onBrandTertiary: arena.aqua,
  border: arena.rim, borderStrong: "#B8404F", divider: "#3A1219",
  muted: arena.muted, mutedSecondary: "#D9A5AE", info: arena.aqua, onInfo: arena.bgDeep,
  success: "#4ADE80", error: "#FF8A8A", warning: "#FFC857", custom_successSoft: "#0F3D2A", custom_errorSoft: "#5C1010",
  custom_gameBg: arena.bg, custom_gameCard: arena.panel, custom_gameCardHi: arena.panelHi,
  custom_gameLine: arena.rim, custom_gameMuted: arena.muted,
  custom_neonCyan: arena.aqua, custom_neonViolet: arena.tealHi, custom_neonMagenta: arena.teal,
  custom_neonAmber: arena.gold, custom_amber: arena.teal, custom_cyan: arena.aqua, custom_neonGreen: "#4ADE80", custom_neonRed: "#FF8A8A",
  custom_examBitsat: fx.fire, custom_examBitsatDeep: "#2A0509", custom_examJee: fx.crimson,
  custom_examJeeDeep: "#2A0509", custom_examComedkGold: arena.gold,
  custom_reading: "#23070D", custom_onReading: "#FFFFFF", custom_infoSoft: "#0E3A36",
  custom_subjectPhysics: "#7DE8DA", custom_subjectChemistry: arena.gold, custom_subjectMaths: "#FFB37A",
  custom_rarityRare: "#7DB4FF", custom_rarityEpic: arena.tealHi, custom_rarityLegendary: arena.gold,
  custom_overlay: arena.scrim,
};
export const rapidSubjectColor = (s?: string) => s === "Physics" ? rapidColors.custom_subjectPhysics
  : s === "Chemistry" ? rapidColors.custom_subjectChemistry : rapidColors.custom_subjectMaths;

export const fonts = {
  regular: "Figtree-400",
  medium: "Figtree-500",
  semibold: "Figtree-600",
  bold: "Figtree-700",
  heavy: "Figtree-800",
};
export const monoFonts = { regular: "RobotoMono-400", medium: "RobotoMono-500", semibold: "RobotoMono-600", bold: "RobotoMono-700" };

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 };
// Rounded search pills draw their own frame; drop the browser's rectangular focus outline.
export const noOutline = (Platform.OS === "web" ? { outlineStyle: "none" } : {}) as TextStyle;
export const radius = { sm: 6, md: 12, lg: 20, pill: 999 };

// Website learning-workspace.css segment tokens, scoped to academic screens.
// Labels accompany these colours; Rapid Fire keeps its existing semantic palette.
export const learningTones = {
  maroon: { line: colors.brandPrimary, soft: colors.brandTertiary, ink: colors.error },
  completed: { line: componentStyle("library.completed").borderTopColor, soft: colors.custom_successSoft, ink: colors.success },
  saved: { line: componentStyle("library.saved").borderTopColor, soft: colors.brandTertiary, ink: colors.brandText },
  active: { line: componentStyle("library.active").borderTopColor, soft: colors.custom_warningSoft, ink: colors.warning },
  error: { line: colors.error, soft: colors.custom_errorSoft, ink: colors.error },
};
export type LearningTone = keyof typeof learningTones;

// All India status pastels, shared by every series surface (Home card, hub, chips, map, graph).
export type SeriesTone = "today" | "done" | "upcoming" | "missed";
export const pastel: Record<SeriesTone, { from: string; to: string; ink: string; body: string; cta: string; label: string }> = {
  today: { from: light.custom_todayFrom, to: light.custom_todayTo, ink: light.custom_todayInk, body: light.custom_todayBody, cta: light.custom_todayCta, label: "Today" },
  done: { from: light.custom_doneFrom, to: light.custom_doneTo, ink: light.custom_doneInk, body: light.custom_doneBody, cta: light.custom_doneCta, label: "Done" },
  upcoming: { from: light.custom_upFrom, to: light.custom_upTo, ink: light.custom_upInk, body: light.custom_upBody, cta: light.custom_upCta, label: "Upcoming" },
  missed: { from: light.custom_missFrom, to: light.custom_missTo, ink: light.custom_missInk, body: light.custom_missBody, cta: light.custom_missCta, label: "Missed" },
};
export const subjectColor = (s?: string) =>
  s === "Physics" ? light.custom_subjectPhysics : s === "Chemistry" ? light.custom_subjectChemistry : s === "Mathematics" ? light.custom_subjectMaths : s === "Biology" ? light.custom_subjectBiology : light.custom_burgundy;

// Readable labels on both bright semantic colours and the dark primary button.
export function foregroundOn(background: string): string {
  if (!/^#[0-9a-f]{6}$/i.test(background)) return dark.onBrandPrimary;
  const channels = [1, 3, 5].map((i) => parseInt(background.slice(i, i + 2), 16) / 255)
    .map((c) => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const luminance = channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  return luminance > 0.179 ? dark.surface : dark.onBrandPrimary;
}

// Shared primitives read the palette from context: academic screens get `colors`,
// Rapid Fire screens wrap themselves in the rapid palette (see src/rapid/ui.tsx).
export const PaletteContext = createContext<ThemeColors>(light);
export function useTheme(): { scheme: ColorScheme; colors: ThemeColors } {
  const palette = useContext(PaletteContext);
  return { scheme: palette === light ? "light" : "dark", colors: palette };
}

type NamedStyles<T> = { [P in keyof T]: ViewStyle | TextStyle | ImageStyle };
export function makeStyles<T extends NamedStyles<T> | NamedStyles<any>>(
  factory: (colors: ThemeColors) => T & NamedStyles<any>,
): () => T {
  return function useStyles(): T {
    const { colors } = useTheme();
    return useMemo(() => StyleSheet.create(factory(colors)), [colors]);
  };
}
