// Design tokens for JEELIVE.AI. Keys match the "color" block of /app/design_guidelines.json.
import { useMemo } from "react";
import { Appearance, StyleSheet, useColorScheme, ViewStyle, TextStyle, ImageStyle } from "react-native";

export type ColorScheme = "light" | "dark";

const light = {
  surface: "#070707",
  onSurface: "#F4EFEA",
  surfaceSecondary: "#121214",
  onSurfaceSecondary: "#F4EFEA",
  surfaceTertiary: "#1E0A0E",
  onSurfaceTertiary: "#FF5266",
  surfaceInverse: "#B0001E",
  onSurfaceInverse: "#FFFFFF",
  muted: "#9A938C",
  brandText: "#FF5266", // readable blood red for text/icons on black (AA)

  brand: "#C8102E",
  onBrand: "#FFFFFF",
  brandPrimary: "#C8102E",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#6E0014",
  onBrandSecondary: "#FFFFFF",
  brandTertiary: "#1E0A0E",
  onBrandTertiary: "#FF5266",

  success: "#34C185",
  onSuccess: "#04140C",
  warning: "#E0A526",
  onWarning: "#1A1204",
  error: "#FF3D55",
  onError: "#FFFFFF",
  info: "#D9B45A",
  onInfo: "#120C02",

  border: "#242426",
  borderStrong: "#36363A",
  divider: "#1C1C1E",

  // Exam & subject identities (user supplied)
  custom_examJee: "#C8102E",
  custom_examJeeDeep: "#4A0010",
  custom_examBitsat: "#E0452B",
  custom_examBitsatDeep: "#7A1A0C",
  custom_examComedk: "#16161A",
  custom_examComedkGold: "#D9B45A",
  custom_series: "#6E0014",
  custom_seriesBright: "#E23A4B",
  custom_burgundy: "#8A0F24",
  custom_subjectPhysics: "#D7263D",
  custom_subjectChemistry: "#8A6A22",
  custom_subjectMaths: "#74747F",
  custom_subjectBiology: "#1F7A55",
  custom_darkCard: "#121214",
  custom_amber: "#7D5F1E",
  custom_cyan: "#D9B45A",
  custom_reading: "#121214",
  custom_onReading: "#F4EFEA",
  custom_successSoft: "#0E2219",
  custom_errorSoft: "#2A0A10",
  custom_warningSoft: "#261D08",
  custom_infoSoft: "#1E0A0E",
  custom_gameBg: "#000000",
  custom_gameCard: "#111113",
  custom_gameCardHi: "#1A1A1D",
  custom_gameLine: "#2A2A2E",
  custom_neonAmber: "#E8C46A",
  custom_neonCyan: "#FF4D5E",
  custom_neonGreen: "#3DDC97",
  custom_neonViolet: "#B0001E",
  custom_neonMagenta: "#FF2E4D",
  custom_rarityRare: "#C0C6CF",
  custom_rarityEpic: "#E23A4B",
  custom_rarityLegendary: "#E8C46A",
  custom_rarityCommon: "#8E8A86",
  custom_neonRed: "#FF3D55",
  custom_gameMuted: "#9A938C",
  custom_overlay: "rgba(0,0,0,0.72)",
  custom_whiteA70: "rgba(255,255,255,0.72)",
  custom_whiteA15: "rgba(255,255,255,0.15)",
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
  regular: "Jakarta-400",
  medium: "Jakarta-500",
  semibold: "Jakarta-600",
  bold: "Jakarta-700",
  heavy: "Jakarta-800",
};

export const space = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32, xxxl: 48 };
export const radius = { sm: 6, md: 12, lg: 20, pill: 999 };

export const subjectColor = (s?: string) =>
  s === "Physics" ? light.custom_subjectPhysics : s === "Chemistry" ? light.custom_subjectChemistry : s === "Mathematics" ? light.custom_subjectMaths : s === "Biology" ? light.custom_subjectBiology : light.custom_burgundy;

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
