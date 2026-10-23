// Design tokens for JEELIVE.AI. Keys match the "color" block of /app/design_guidelines.json.
import { useMemo } from "react";
import { Appearance, StyleSheet, useColorScheme } from "react-native";

export type ColorScheme = "light" | "dark";

const light = {
  surface: "#F5F7FC",
  onSurface: "#0B1F2A",
  surfaceSecondary: "#FFFFFF",
  onSurfaceSecondary: "#0B1F2A",
  surfaceTertiary: "#FFF5F3",
  onSurfaceTertiary: "#991B1B",
  surfaceInverse: "#0C1220",
  onSurfaceInverse: "#FFFFFF",
  muted: "#64748B",

  brand: "#2459D8",
  onBrand: "#FFFFFF",
  brandPrimary: "#2459D8",
  onBrandPrimary: "#FFFFFF",
  brandSecondary: "#0B2D80",
  onBrandSecondary: "#FFFFFF",
  brandTertiary: "#FFF5F3",
  onBrandTertiary: "#991B1B",

  success: "#15803D",
  onSuccess: "#FFFFFF",
  warning: "#B45309",
  onWarning: "#FFFFFF",
  error: "#B91C1C",
  onError: "#FFFFFF",
  info: "#1D4ED8",
  onInfo: "#FFFFFF",

  border: "#E2E8F0",
  borderStrong: "#CBD5E1",
  divider: "#E2E8F0",

  // Exam & subject identities (user supplied)
  custom_examJee: "#C8102E",
  custom_examJeeDeep: "#7A0A1C",
  custom_examBitsat: "#F97316",
  custom_examBitsatDeep: "#B4470B",
  custom_examComedk: "#0A0A0A",
  custom_examComedkGold: "#D4AF37",
  custom_series: "#0B2D80",
  custom_seriesBright: "#2F6BFF",
  custom_burgundy: "#991B1B",
  custom_subjectPhysics: "#2459D8",
  custom_subjectChemistry: "#087B68",
  custom_subjectMaths: "#B92B45",
  custom_darkCard: "#141D2D",
  custom_amber: "#9E550A",
  custom_cyan: "#087DA2",
  custom_reading: "#FFFFFF",
  custom_onReading: "#0B1F2A",
  custom_successSoft: "#DCFCE7",
  custom_errorSoft: "#FEE2E2",
  custom_warningSoft: "#FEF3C7",
  custom_infoSoft: "#E0EAFF",
  custom_gameBg: "#070B18",
  custom_gameCard: "#111833",
  custom_gameCardHi: "#1A2450",
  custom_gameLine: "#26325E",
  custom_neonAmber: "#FBBF24",
  custom_neonCyan: "#22D3EE",
  custom_neonGreen: "#34D399",
  custom_neonViolet: "#A78BFA",
  custom_neonMagenta: "#E879F9",
  custom_rarityRare: "#38BDF8",
  custom_rarityEpic: "#C084FC",
  custom_rarityLegendary: "#FBBF24",
  custom_rarityCommon: "#94A3B8",
  custom_neonRed: "#FB7185",
  custom_gameMuted: "#94A3C7",
  custom_overlay: "rgba(12,18,32,0.55)",
  custom_whiteA70: "rgba(255,255,255,0.72)",
  custom_whiteA15: "rgba(255,255,255,0.15)",
};

export type ThemeColors = typeof light;

export const defaultScheme = "light" satisfies ColorScheme;
export const themes: { light: ThemeColors; dark?: ThemeColors } = { light };

export function setColorScheme(scheme: ColorScheme | null) {
  Appearance.setColorScheme?.(scheme ?? "unspecified");
}
setColorScheme?.(themes.dark ? null : defaultScheme);

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
  s === "Physics" ? light.custom_subjectPhysics : s === "Chemistry" ? light.custom_subjectChemistry : s === "Mathematics" ? light.custom_subjectMaths : light.custom_cyan;

export function useTheme(): { scheme: ColorScheme; colors: ThemeColors } {
  const system = useColorScheme();
  const scheme: ColorScheme = (system === "light" || system === "dark") && themes[system] ? system : defaultScheme;
  return { scheme, colors: themes[scheme] ?? themes.light };
}

export function makeStyles<T extends StyleSheet.NamedStyles<T> | StyleSheet.NamedStyles<any>>(
  factory: (colors: ThemeColors) => T & StyleSheet.NamedStyles<any>,
): () => T {
  return function useStyles(): T {
    const { colors } = useTheme();
    return useMemo(() => StyleSheet.create(factory(colors)), [colors]);
  };
}
