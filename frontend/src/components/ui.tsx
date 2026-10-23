import React, { useEffect } from "react";
import { ActivityIndicator, Pressable, StyleProp, Text as RNText, TextProps, TextStyle, View, ViewStyle } from "react-native";
import Animated, { useAnimatedStyle, useSharedValue, withRepeat, withTiming, withSpring } from "react-native-reanimated";
import MaterialDesignIcons from "@react-native-vector-icons/material-design-icons";
import * as Haptics from "expo-haptics";
import { fonts, makeStyles, radius, space, useTheme } from "@/src/theme";

export const Icon = MaterialDesignIcons;
export type IconName = React.ComponentProps<typeof MaterialDesignIcons>["name"];

type W = "regular" | "medium" | "semibold" | "bold" | "heavy";
export function T({ w = "regular", size = 14, color, style, ...p }: TextProps & { w?: W; size?: number; color?: string }) {
  const { colors } = useTheme();
  return <RNText {...p} maxFontSizeMultiplier={1.6} style={[{ fontFamily: fonts[w], fontSize: size, color: color ?? colors.onSurface, lineHeight: Math.round(size * 1.35) }, style as StyleProp<TextStyle>]} />;
}

export const tap = (style: "light" | "medium" = "light") => {
  Haptics.impactAsync(style === "light" ? Haptics.ImpactFeedbackStyle.Light : Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
};
// Distinct buzz for right / wrong / big moments.
export const buzz = (kind: "success" | "error" | "warning") => {
  Haptics.notificationAsync(kind === "success" ? Haptics.NotificationFeedbackType.Success : kind === "error" ? Haptics.NotificationFeedbackType.Error : Haptics.NotificationFeedbackType.Warning).catch(() => {});
};

const AnimatedPressable = Animated.createAnimatedComponent(Pressable);

export function Press({ onPress, style, children, disabled, testID, accessibilityLabel, haptic = true, scaleTo = 0.97 }: {
  onPress?: () => void; style?: StyleProp<ViewStyle>; children: React.ReactNode; disabled?: boolean; testID?: string; accessibilityLabel?: string; haptic?: boolean; scaleTo?: number;
}) {
  const s = useSharedValue(1);
  const a = useAnimatedStyle(() => ({ transform: [{ scale: s.value }] }));
  return (
    <AnimatedPressable
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityState={{ disabled: !!disabled }}
      disabled={disabled}
      onPressIn={() => (s.value = withSpring(scaleTo, { damping: 18, stiffness: 400 }))}
      onPressOut={() => (s.value = withSpring(1, { damping: 18, stiffness: 400 }))}
      onPress={() => {
        if (haptic) tap();
        onPress?.();
      }}
      style={[a, style, disabled && { opacity: 0.5 }]}
    >
      {children}
    </AnimatedPressable>
  );
}

export function Button({ label, onPress, kind = "primary", icon, busy, disabled, testID, color, style }: {
  label: string; onPress?: () => void; kind?: "primary" | "secondary" | "ghost" | "danger"; icon?: IconName; busy?: boolean; disabled?: boolean; testID?: string; color?: string; style?: StyleProp<ViewStyle>;
}) {
  const { colors } = useTheme();
  const bg = kind === "primary" ? color ?? colors.brandPrimary : kind === "danger" ? colors.error : kind === "secondary" ? colors.surfaceSecondary : "transparent";
  const fg = kind === "primary" || kind === "danger" ? colors.onBrandPrimary : color ?? colors.brandPrimary;
  return (
    <Press testID={testID} onPress={onPress} disabled={disabled || busy} accessibilityLabel={label}
      style={[{ minHeight: 50, borderRadius: radius.md, backgroundColor: bg, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: space.sm, paddingHorizontal: space.lg, borderWidth: kind === "secondary" ? 1 : 0, borderColor: colors.border }, style]}>
      {busy ? <ActivityIndicator color={fg} /> : icon ? <Icon name={icon} size={19} color={fg} /> : null}
      <T w="bold" size={15} color={fg}>{label}</T>
    </Press>
  );
}

const useBoxStyles = makeStyles((c) => ({
  card: { backgroundColor: c.surfaceSecondary, borderRadius: radius.lg, padding: space.lg, borderWidth: 1, borderColor: c.border, shadowColor: c.surfaceInverse, shadowOpacity: 0.06, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 2 },
  notice: { flexDirection: "row", gap: space.sm, padding: space.md, borderRadius: radius.md, alignItems: "flex-start" },
  chip: { height: 44, paddingHorizontal: space.md, borderRadius: radius.pill, flexDirection: "row", alignItems: "center", gap: 6, borderWidth: 1, flexShrink: 0 },
  empty: { alignItems: "center", padding: space.xl, gap: space.sm },
}));

export function Card({ children, style, testID }: { children: React.ReactNode; style?: StyleProp<ViewStyle>; testID?: string }) {
  const st = useBoxStyles();
  return <View testID={testID} style={[st.card, style]}>{children}</View>;
}

export function Notice({ tone = "info", icon, children, testID }: { tone?: "info" | "warning" | "error" | "success"; icon?: IconName; children: React.ReactNode; testID?: string }) {
  const { colors } = useTheme();
  const st = useBoxStyles();
  const map = { info: [colors.custom_infoSoft, colors.info], warning: [colors.custom_warningSoft, colors.warning], error: [colors.custom_errorSoft, colors.error], success: [colors.custom_successSoft, colors.success] } as const;
  const [bg, fg] = map[tone];
  return (
    <View testID={testID} style={[st.notice, { backgroundColor: bg }]} accessibilityRole="alert">
      <Icon name={icon ?? (tone === "error" ? "alert-circle-outline" : tone === "warning" ? "alert-outline" : tone === "success" ? "check-circle-outline" : "information-outline")} size={18} color={fg} />
      <View style={{ flex: 1 }}>{typeof children === "string" ? <T size={13} color={fg} w="medium">{children}</T> : children}</View>
    </View>
  );
}

export function Chip({ label, active, onPress, color, testID, icon, count }: { label: string; active?: boolean; onPress?: () => void; color?: string; testID?: string; icon?: IconName; count?: number }) {
  const { colors } = useTheme();
  const st = useBoxStyles();
  const c = color ?? colors.brandPrimary;
  return (
    <Press testID={testID} onPress={onPress} accessibilityLabel={label} style={[st.chip, { backgroundColor: active ? c : colors.surfaceSecondary, borderColor: active ? c : colors.border }]}>
      {icon ? <Icon name={icon} size={15} color={active ? colors.onBrandPrimary : c} /> : null}
      <T w="bold" size={13} color={active ? colors.onBrandPrimary : colors.onSurface}>{label}</T>
      {count !== undefined ? <T w="bold" size={11} color={active ? colors.onBrandPrimary : colors.muted}>{count}</T> : null}
    </Press>
  );
}

export function Empty({ icon = "book-open-page-variant-outline", title, body, action, testID }: { icon?: IconName; title: string; body?: string; action?: React.ReactNode; testID?: string }) {
  const { colors } = useTheme();
  const st = useBoxStyles();
  return (
    <View testID={testID} style={st.empty}>
      <View style={{ width: 64, height: 64, borderRadius: 32, backgroundColor: colors.custom_infoSoft, alignItems: "center", justifyContent: "center" }}>
        <Icon name={icon} size={30} color={colors.brandPrimary} />
      </View>
      <T w="bold" size={17} style={{ textAlign: "center" }}>{title}</T>
      {body ? <T size={13} color={colors.muted} style={{ textAlign: "center" }}>{body}</T> : null}
      {action}
    </View>
  );
}

export function ErrorBox({ error, retry, testID = "error-box" }: { error?: string; retry?: () => void; testID?: string }) {
  const { colors } = useTheme();
  if (!error) return null;
  return (
    <Notice tone="error" testID={testID}>
      <T size={13} w="medium" color={colors.error}>{error}</T>
      {retry ? (
        <Press testID={testID + "-retry"} onPress={retry} style={{ marginTop: 6, alignSelf: "flex-start" }}>
          <T w="bold" size={13} color={colors.brandPrimary}>Retry</T>
        </Press>
      ) : null}
    </Notice>
  );
}

export function Skeleton({ h = 80, style }: { h?: number; style?: StyleProp<ViewStyle> }) {
  const { colors } = useTheme();
  const o = useSharedValue(0.5);
  useEffect(() => {
    o.value = withRepeat(withTiming(1, { duration: 700 }), -1, true);
  }, [o]);
  const a = useAnimatedStyle(() => ({ opacity: o.value }));
  return <Animated.View style={[{ height: h, borderRadius: radius.lg, backgroundColor: colors.border }, a, style]} />;
}

export function Header({ title, eyebrow, onBack, right, color, testID }: { title: string; eyebrow?: string; onBack?: () => void; right?: React.ReactNode; color?: string; testID?: string }) {
  const { colors } = useTheme();
  return (
    <View testID={testID} style={{ flexDirection: "row", alignItems: "center", gap: space.sm, paddingHorizontal: space.lg, paddingBottom: space.md }}>
      {onBack ? (
        <Press testID="header-back-button" onPress={onBack} accessibilityLabel="Back" style={{ width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border }}>
          <Icon name="arrow-left" size={22} color={colors.onSurface} />
        </Press>
      ) : null}
      <View style={{ flex: 1 }}>
        {eyebrow ? <T w="bold" size={11} color={color ?? colors.muted} style={{ letterSpacing: 1.2 }}>{eyebrow.toUpperCase()}</T> : null}
        <T w="heavy" size={22} numberOfLines={2}>{title}</T>
      </View>
      {right}
    </View>
  );
}

export function Stat({ label, value, color, testID }: { label: string; value: string | number; color?: string; testID?: string }) {
  const { colors } = useTheme();
  return (
    <View testID={testID} style={{ flex: 1, minWidth: 90, padding: space.md, borderRadius: radius.md, backgroundColor: colors.surface, gap: 2 }}>
      <T w="heavy" size={22} color={color ?? colors.onSurface}>{value}</T>
      <T size={12} color={colors.muted} w="medium">{label}</T>
    </View>
  );
}

export function Sheet({ visible, onClose, children, testID }: { visible: boolean; onClose: () => void; children: React.ReactNode; testID?: string }) {
  const { colors } = useTheme();
  if (!visible) return null;
  return (
    <View style={{ position: "absolute", left: 0, right: 0, top: 0, bottom: 0, zIndex: 50 }}>
      <Pressable testID={(testID ?? "sheet") + "-backdrop"} onPress={onClose} style={{ flex: 1, backgroundColor: colors.custom_overlay }} />
      <View testID={testID} style={{ backgroundColor: colors.surfaceSecondary, borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: space.xl, paddingBottom: space.xxl, gap: space.md, maxHeight: "85%" }}>
        <View style={{ alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: colors.borderStrong, marginTop: -8 }} />
        {children}
      </View>
    </View>
  );
}
