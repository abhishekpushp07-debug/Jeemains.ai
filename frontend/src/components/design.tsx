import React, { useEffect, useId } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import Svg, { Circle, Defs, LinearGradient as SvgGradient, Stop } from "react-native-svg";
import Animated, { Easing, SlideInDown, FadeIn, useAnimatedProps, useReducedMotion, useSharedValue, withTiming } from "react-native-reanimated";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { colors, pastel, radius, SeriesTone, space } from "@/src/theme";
import { IconName, Press, T } from "./ui";
import { Glyph } from "./Glyph";

/** Quiet, widely spaced CAPITAL heading with an optional lowercase "view all ›" link. */
export function SectionLabel({ title, action, onAction, right, testID, actionTestID }: {
  title: string; action?: string; onAction?: () => void; right?: React.ReactNode; testID?: string; actionTestID?: string;
}) {
  return <View style={styles.sectionRow}>
    <T testID={testID} w="bold" size={12} color={colors.custom_eyebrow} style={styles.sectionText}>{title.toUpperCase()}</T>
    {right}
    {onAction ? <Press testID={actionTestID} onPress={onAction} accessibilityLabel={`${action || "View all"} ${title}`} style={styles.sectionAction}>
      <T size={14} color={colors.custom_softText}>{action || "view all"}</T>
      <Glyph name="chevron-right" size={16} color={colors.custom_softText} />
    </Press> : null}
  </View>;
}

/** White hairline card with soft round corners. */
export function DCard({ children, style, testID }: { children: React.ReactNode; style?: StyleProp<ViewStyle>; testID?: string }) {
  return <View testID={testID} style={[styles.card, style]}>{children}</View>;
}

/** All India status pastel surface (peach-rose today, green done, teal upcoming, sand missed). */
export function PastelSurface({ tone, style, children, testID }: { tone: SeriesTone; style?: StyleProp<ViewStyle>; children?: React.ReactNode; testID?: string }) {
  const p = pastel[tone];
  return <LinearGradient testID={testID} colors={[p.from, p.to]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={style}>{children}</LinearGradient>;
}

type PillKind = "light" | "dark" | "brand" | "outline" | "teal" | "danger";
export function Pill({ label, onPress, kind = "light", icon, iconRight, busy, disabled, testID, style, ink, bg, size = "md", accessibilityLabel }: {
  label: string; onPress?: () => void; kind?: PillKind; icon?: IconName; iconRight?: IconName; busy?: boolean; disabled?: boolean; testID?: string;
  style?: StyleProp<ViewStyle>; ink?: string; bg?: string; size?: "sm" | "md" | "lg"; accessibilityLabel?: string;
}) {
  const base = {
    light: [colors.onSurface, colors.onSurfaceInverse, colors.onSurface],
    dark: [colors.custom_pastelInk, colors.custom_todayCta, colors.custom_pastelInk],
    brand: [colors.brandPrimary, colors.onBrandPrimary, colors.brandPrimary],
    outline: [colors.custom_card, colors.onSurface, colors.custom_cardLineStrong],
    teal: ["transparent", colors.custom_qMarkedInk, colors.custom_qMarked],
    danger: ["transparent", colors.error, colors.error],
  }[kind];
  const fill = bg ?? base[0], fg = ink ?? base[1];
  const h = size === "lg" ? 54 : size === "sm" ? 44 : 50;
  return <Press testID={testID} onPress={onPress} disabled={disabled || busy} accessibilityLabel={accessibilityLabel || label} scaleTo={0.97}
    style={[styles.pill, { minHeight: h, backgroundColor: fill, borderColor: bg ?? base[2], borderWidth: kind === "outline" || kind === "teal" || kind === "danger" ? 1 : 0 }, style]}>
    {busy ? <ActivityIndicator color={fg} /> : icon ? <Glyph name={icon} size={18} color={fg} stroke={1.8} /> : null}
    <T testID={testID ? `${testID}-label` : undefined} w="bold" size={size === "sm" ? 13.5 : 15} color={fg} numberOfLines={1}>{label}</T>
    {iconRight && !busy ? <Glyph name={iconRight} size={18} color={fg} stroke={1.8} /> : null}
  </Press>;
}

/** Rounded segmented control: the selected segment turns black. */
export function Segmented<K extends string>({ items, value, onChange, prefix, testID, compact }: {
  items: { key: K; label: string; sub?: string; testID?: string; subTestID?: string; labelTestID?: string; a11y?: string }[];
  value: K; onChange: (key: K) => void; prefix: string; testID?: string; compact?: boolean;
}) {
  return <View testID={testID} accessibilityRole="tablist" style={styles.segment}>
    {items.map(item => {
      const on = item.key === value;
      return <Press key={item.key} testID={item.testID ?? `${prefix}-${item.key}`} accessibilityRole="tab" accessibilityState={{ selected: on }} accessibilityLabel={item.a11y ?? item.label}
        onPress={() => onChange(item.key)} scaleTo={0.98} style={[styles.segmentItem, compact && { minHeight: 44 }, on && styles.segmentOn]}>
        <T testID={item.labelTestID} w={on ? "bold" : "semibold"} size={13} numberOfLines={1} color={on ? colors.onSurfaceInverse : colors.custom_softText}>{item.label}</T>
        {item.sub !== undefined ? <T testID={item.subTestID} w="bold" size={10.5} color={on ? colors.custom_dim : colors.custom_eyebrow}>{item.sub}</T> : null}
      </Press>;
    })}
  </View>;
}

export function ScreenHeader({ title, eyebrow, onBack, right, testID, backTestID, eyebrowColor, titleColor }: {
  title: string; eyebrow?: string; onBack?: () => void; right?: React.ReactNode; testID?: string; backTestID?: string; eyebrowColor?: string; titleColor?: string;
}) {
  return <View testID={testID} style={styles.header}>
    {onBack ? <Press testID={backTestID || "header-back-button"} onPress={onBack} accessibilityLabel="Back" style={styles.round}>
      <Glyph name="chevron-left" size={22} color={colors.onSurface} stroke={1.8} />
    </Press> : null}
    <View style={{ flex: 1 }}>
      {eyebrow ? <T w="bold" size={11} color={eyebrowColor ?? colors.custom_eyebrow} style={{ letterSpacing: 2.2 }} numberOfLines={2}>{eyebrow.toUpperCase()}</T> : null}
      <T testID={testID ? `${testID}-title` : undefined} w="heavy" size={21} color={titleColor} numberOfLines={2}>{title}</T>
    </View>
    {right}
  </View>;
}

export function RoundButton({ icon, onPress, testID, label, color, active, style }: { icon: IconName; onPress: () => void; testID?: string; label: string; color?: string; active?: boolean; style?: StyleProp<ViewStyle> }) {
  return <Press testID={testID} onPress={onPress} accessibilityLabel={label} accessibilityState={active !== undefined ? { selected: active } : undefined} style={[styles.round, style]}>
    <Glyph name={icon} size={20} color={color ?? colors.custom_softText} stroke={1.8} />
  </Press>;
}

export function StatusLine({ color, label, testID }: { color: string; label: string; testID?: string }) {
  return <View testID={testID} style={styles.statusLine}>
    <View style={[styles.dot, { backgroundColor: color }]} />
    <T testID={testID ? `${testID}-label` : undefined} w="bold" size={10.5} color={color} style={{ letterSpacing: 1.4 }} numberOfLines={1}>{label.toUpperCase()}</T>
  </View>;
}

/** Soft grey circle holding a hairline icon (inverted = black circle, white icon). */
export function IconCircle({ icon, color, bg, size = 40, line }: { icon: IconName; color: string; bg?: string; size?: number; line?: string }) {
  return <View style={{ width: size, height: size, borderRadius: size / 2, backgroundColor: bg ?? colors.custom_cardRaised, borderWidth: 1, borderColor: line ?? colors.custom_cardLine, alignItems: "center", justifyContent: "center" }}>
    <Glyph name={icon} size={Math.round(size * 0.48)} color={color} />
  </View>;
}

/** Grouped settings list ("SECURITY", "PRIVACY", "ACCOUNT"). */
export function GroupList({ title, children, testID }: { title: string; children: React.ReactNode; testID?: string }) {
  const rows = React.Children.toArray(children).filter(Boolean);
  return <View testID={testID} style={{ gap: space.md }}>
    <SectionLabel title={title} />
    <View style={styles.group}>
      {rows.map((row, i) => <View key={i} style={i ? styles.groupDivider : undefined}>{row}</View>)}
    </View>
  </View>;
}

export function ListRow({ icon, label, sub, onPress, testID, danger, busy }: { icon: IconName; label: string; sub?: string; onPress: () => void; testID?: string; danger?: boolean; busy?: boolean }) {
  const ink = danger ? colors.error : colors.onSurface;
  return <Press testID={testID} onPress={onPress} disabled={busy} accessibilityLabel={label} scaleTo={0.99} style={styles.listRow}>
    <IconCircle icon={icon} color={danger ? colors.error : colors.onSurface} size={40} />
    <View style={{ flex: 1, gap: 1 }}>
      <T testID={testID ? `${testID}-label` : undefined} w="semibold" size={15.5} color={ink}>{label}</T>
      {sub ? <T size={12.5} color={colors.muted}>{sub}</T> : null}
    </View>
    {busy ? <ActivityIndicator color={colors.muted} /> : <Glyph name="chevron-right" size={18} color={colors.custom_dim} />}
  </Press>;
}

const AnimatedCircle = Animated.createAnimatedComponent(Circle);
/** Apple-Fitness style progress ring drawn in code (no image weight). */
export function ProgressRing({ size, stroke, value, track, color, gradient, children, testID, label }: {
  size: number; stroke: number; value: number; track: string; color?: string; gradient?: [string, string]; children?: React.ReactNode; testID?: string; label?: string;
}) {
  const reduced = useReducedMotion();
  const id = useId().replace(/[^a-z0-9]/gi, "");
  const r = (size - stroke) / 2, c = 2 * Math.PI * r;
  const v = Math.max(0, Math.min(1, value || 0));
  const offset = useSharedValue(reduced ? c * (1 - v) : c);
  useEffect(() => {
    offset.value = reduced ? c * (1 - v) : withTiming(c * (1 - v), { duration: 900, easing: Easing.out(Easing.cubic) });
  }, [v, c, reduced, offset]);
  const props = useAnimatedProps(() => ({ strokeDashoffset: offset.value }));
  return <View testID={testID} accessibilityRole="progressbar" accessibilityLabel={label} accessibilityValue={{ min: 0, max: 100, now: Math.round(v * 100) }}
    style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
    <Svg width={size} height={size} style={{ position: "absolute", transform: [{ rotate: "-90deg" }] }}>
      {gradient ? <Defs><SvgGradient id={`ring${id}`} x1="0" y1="0" x2="1" y2="1"><Stop offset="0" stopColor={gradient[0]} /><Stop offset="1" stopColor={gradient[1]} /></SvgGradient></Defs> : null}
      <Circle cx={size / 2} cy={size / 2} r={r} stroke={track} strokeWidth={stroke} fill="none" />
      {v > 0 ? <AnimatedCircle cx={size / 2} cy={size / 2} r={r} stroke={gradient ? `url(#ring${id})` : color} strokeWidth={stroke} fill="none" strokeLinecap="round" strokeDasharray={`${c} ${c}`} animatedProps={props} /> : null}
    </Svg>
    {children}
  </View>;
}

/** Bottom sheet: rises from the bottom, handle + title + close. */
export function DSheet({ visible, onClose, title, children, testID, closeTestID, scroll = true }: {
  visible: boolean; onClose: () => void; title?: string; children: React.ReactNode; testID?: string; closeTestID?: string; scroll?: boolean;
}) {
  const insets = useSafeAreaInsets();
  const reduced = useReducedMotion();
  if (!visible) return null;
  // A transparent Modal covers the whole window (tab bar included), wherever the sheet is declared.
  return <Modal visible transparent animationType="none" statusBarTranslucent onRequestClose={onClose}>
    <View style={styles.sheetLayer}>
    <Animated.View entering={reduced ? undefined : FadeIn.duration(160)} style={StyleSheet.absoluteFill}>
      <Pressable testID={(testID ?? "sheet") + "-backdrop"} accessibilityLabel="Close" onPress={onClose} style={[StyleSheet.absoluteFill, { backgroundColor: colors.custom_shade }]} />
    </Animated.View>
    <Animated.View testID={testID} entering={reduced ? undefined : SlideInDown.duration(260)} style={[styles.sheet, { paddingBottom: insets.bottom + space.lg }]}>
      <View style={styles.handle} />
      {title ? <View style={styles.sheetTitle}>
        <T w="heavy" size={19} style={{ flex: 1 }}>{title}</T>
        <Press testID={closeTestID ?? (testID ? `${testID}-close` : undefined)} onPress={onClose} accessibilityLabel="Close" style={styles.sheetClose}>
          <Glyph name="close" size={18} color={colors.onSurface} stroke={1.8} />
        </Press>
      </View> : null}
      {scroll ? <ScrollView contentContainerStyle={{ gap: space.md, paddingBottom: space.xs }} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">{children}</ScrollView>
        : <View style={{ gap: space.md }}>{children}</View>}
    </Animated.View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  sectionRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: space.sm, minHeight: 28 },
  sectionText: { letterSpacing: 2.6, flexShrink: 1 },
  sectionAction: { minHeight: 44, minWidth: 44, flexDirection: "row", alignItems: "center", justifyContent: "flex-end", gap: 2, paddingLeft: space.sm },
  card: { backgroundColor: colors.custom_card, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLine, padding: space.lg },
  pill: { borderRadius: radius.pill, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8, paddingHorizontal: 20 },
  segment: { flexDirection: "row", padding: 4, gap: 2, borderRadius: radius.pill, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine },
  segmentItem: { flex: 1, minWidth: 0, minHeight: 42, borderRadius: radius.pill, alignItems: "center", justifyContent: "center", paddingHorizontal: 6, paddingVertical: 3 },
  segmentOn: { backgroundColor: colors.onSurface },
  header: { flexDirection: "row", alignItems: "center", gap: space.md, paddingHorizontal: space.lg, paddingBottom: space.md },
  round: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLineStrong, alignItems: "center", justifyContent: "center" },
  statusLine: { flexDirection: "row", alignItems: "center", gap: 6, flexShrink: 1 },
  dot: { width: 7, height: 7, borderRadius: 4 },
  group: { backgroundColor: colors.custom_card, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLine, overflow: "hidden" },
  groupDivider: { borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  listRow: { flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 68, paddingHorizontal: space.lg, paddingVertical: space.sm },
  sheetLayer: { flex: 1, justifyContent: "flex-end" },
  sheet: { backgroundColor: colors.custom_card, borderTopLeftRadius: 28, borderTopRightRadius: 28, paddingHorizontal: space.xl, paddingTop: space.md, gap: space.md, maxHeight: "88%" },
  handle: { alignSelf: "center", width: 40, height: 4, borderRadius: 2, backgroundColor: colors.custom_qFreshLine },
  sheetTitle: { flexDirection: "row", alignItems: "center", gap: space.sm },
  sheetClose: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.custom_cardRaised, alignItems: "center", justifyContent: "center" },
});
