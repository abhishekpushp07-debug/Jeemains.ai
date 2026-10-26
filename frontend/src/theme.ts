// Design tokens for JEELIVE.AI. Keys match the "color" block of /app/design_guidelines.json.
import { useMemo } from "react";
import { Appearance, StyleSheet, useColorScheme, ViewStyle, TextStyle, ImageStyle } from "react-native";

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

  // Current website uses a unified red identity; semantic study/game colours remain distinct.
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

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 };
export const radius = { sm: 6, md: 12, lg: 20, pill: 999 };

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
