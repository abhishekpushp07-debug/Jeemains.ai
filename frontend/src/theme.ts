// Design tokens for JEELIVE.AI. Keys match the "color" block of /app/design_guidelines.json.
import { useMemo } from "react";
import { Appearance, StyleSheet, useColorScheme, ViewStyle, TextStyle, ImageStyle } from "react-native";
import { componentStyle, homeDesign, websiteDesign } from "./websiteDesign";

export type ColorScheme = "light" | "dark";

const light = {
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
  custom_subjectMaths: "#D9B1E9",
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
  custom_neonViolet: "#D9B1E9",
  custom_neonMagenta: "#FF6974",
  custom_rarityRare: "#C0C6CF",
  custom_rarityEpic: "#D9B1E9",
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
};

export type ThemeColors = typeof light;

export const defaultScheme = "dark" satisfies ColorScheme;
export const themes: { light: ThemeColors; dark?: ThemeColors } = { light, dark: light };

export function setColorScheme(scheme: ColorScheme | null) {
  Appearance.setColorScheme?.(scheme ?? "unspecified");
}
setColorScheme?.(defaultScheme); // the luxury theme is always dark

export const colors = light;

export const fonts = {
  regular: "Figtree-400",
  medium: "Figtree-500",
  semibold: "Figtree-600",
  bold: "Figtree-700",
  heavy: "Figtree-800",
};
export const monoFonts = { regular: "RobotoMono-400", medium: "RobotoMono-500", semibold: "RobotoMono-600", bold: "RobotoMono-700" };

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 };
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

export type ExamCardKind = "jee" | "live" | "bitsat" | "comedk";
export function examCardColors(kind: ExamCardKind) {
  const { card, cta } = homeDesign(kind === "jee" ? "jee-main" : kind === "live" ? "all-india" : kind);
  return { background: card.default.backgroundColor, layers: card.default.backgroundImage,
    ink: card.h2.color, accent: card.small.color, muted: card.p.color, line: card.default.borderTopColor,
    button: cta.backgroundColor, buttonInk: cta.color, buttonLayers: cta.backgroundImage,
    iconBackground: colors.custom_webGlass, shadow: card.default.boxShadow,
    innerLine: card.after.borderTopColor, shine: card.before.backgroundImage,
  };
}

// Selector-scoped states from the export; these never recolour the RF palette.
export const academicStyles = {
  pyq: componentStyle("pyq.default"), score: componentStyle("result.score"),
  tab: componentStyle("tab.default"), selectedTab: componentStyle("tab.selected"),
  source: componentStyle("solution.source"), original: componentStyle("solution.original"),
};
export const seriesHome = websiteDesign.home_cards["all-india"];

export const subjectColor = (s?: string) =>
  s === "Physics" ? light.custom_subjectPhysics : s === "Chemistry" ? light.custom_subjectChemistry : s === "Mathematics" ? light.custom_subjectMaths : s === "Biology" ? light.custom_subjectBiology : light.custom_burgundy;

// Readable labels on both bright semantic colours and the dark primary button.
export function foregroundOn(background: string): string {
  if (!/^#[0-9a-f]{6}$/i.test(background)) return light.onBrandPrimary;
  const channels = [1, 3, 5].map((i) => parseInt(background.slice(i, i + 2), 16) / 255)
    .map((c) => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
  const luminance = channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  return luminance > 0.179 ? light.surface : light.onBrandPrimary;
}

export function useTheme(): { scheme: ColorScheme; colors: ThemeColors } {
  const system = useColorScheme();
  const scheme: ColorScheme = (system === "light" || system === "dark") && themes[system] ? system : defaultScheme;
  return { scheme, colors: themes[scheme] ?? themes.light };
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
