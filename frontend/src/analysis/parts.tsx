import React, { useState } from "react";
import { StyleSheet, View } from "react-native";
import { ScrollView } from "react-native-gesture-handler";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";
import { An, Drill, Open, OUT_ICON, OUT_TONE, RESULT, TAG, TONE, Tone, index, mmss, slug } from "./format";

/** One white card of the analysis: small caps kicker, title, a one-line note, then the content. */
export function Block({ id, kicker, title, note, action, children }: { id: string; kicker?: string; title: string; note?: string; action?: React.ReactNode; children?: React.ReactNode }) {
  return <View testID={"a2-block-" + id} style={styles.block}>
    <View style={styles.blockHead}>
      <View style={{ flex: 1, gap: 2 }}>
        {kicker ? <T w="heavy" size={10} color={colors.brandText} style={styles.kicker}>{kicker}</T> : null}
        <T w="heavy" size={18}>{title}</T>
        {note ? <T size={12.5} color={colors.muted}>{note}</T> : null}
      </View>
      {action}
    </View>
    {children}
  </View>;
}

/** A number with its label. With `ids` it opens those questions. */
export function Tile({ id, label, value, sub, tone = "plain", ids, onDrill }: { id: string; label: string; value: React.ReactNode; sub?: string; tone?: Tone; ids?: string[]; onDrill?: Drill }) {
  const t = TONE[tone], tappable = !!ids?.length && !!onDrill;
  const body = <>
    {tone !== "plain" ? <View style={[styles.tileDot, { backgroundColor: t.fill }]} /> : null}
    <T size={11} w="bold" color={colors.custom_eyebrow} numberOfLines={1} style={{ paddingRight: 12 }}>{label}</T>
    <T testID={`a2-tile-${id}-value`} w="heavy" size={21} color={tone === "plain" || tone === "mute" ? colors.onSurface : t.ink} numberOfLines={1} adjustsFontSizeToFit>{value}</T>
    {sub ? <T size={11} color={colors.muted}>{sub}</T> : null}
    {tappable ? <T size={11} w="bold" color={colors.brandText}>Sawaal dekho ›</T> : null}
  </>;
  return tappable
    ? <Press testID={"a2-tile-" + id} onPress={() => onDrill!(label, ids!)} accessibilityLabel={`${label}: ${typeof value === "string" || typeof value === "number" ? value : ""}. Sawaal dekho`} style={styles.tile}>{body}</Press>
    : <View testID={"a2-tile-" + id} style={styles.tile}>{body}</View>;
}
export const Tiles = ({ children, cols = 2 }: { children: React.ReactNode; cols?: 2 | 3 }) => (
  <View style={styles.tiles}>{React.Children.toArray(children).filter(Boolean).map((c, i) => <View key={i} style={cols === 3 ? styles.third : styles.half}>{c}</View>)}</View>
);

export function TagChip({ tag, copy }: { tag?: string | null; copy: An["copy"] }) {
  if (!tag || !TAG[tag]) return <View style={[styles.tag, { backgroundColor: TONE.mute.soft }]}><T size={10.5} w="bold" color={colors.muted}>—</T></View>;
  const [tone, icon] = TAG[tag], t = TONE[tone];
  return <View style={[styles.tag, { backgroundColor: t.soft }]} accessibilityLabel={copy.tags[tag][1]}>
    <Icon name={icon} size={11} color={t.ink} />
    <T size={10.5} w="bold" color={t.ink} numberOfLines={1}>{copy.tags[tag][0]}</T>
  </View>;
}
export const ToneTag = ({ label, tone, icon }: { label: string; tone: Tone; icon?: IconName }) => (
  <View style={[styles.tag, { backgroundColor: TONE[tone].soft }]}>
    {icon ? <Icon name={icon} size={11} color={TONE[tone].ink} /> : null}
    <T size={10.5} w="bold" color={TONE[tone].ink} numberOfLines={1}>{label}</T>
  </View>
);

export function Locked({ id, title, text, icon = "lock-outline", testID }: { id: string; title: string; text: string; icon?: IconName; testID?: string }) {
  return <View testID={testID || "a2-locked-" + id} style={styles.locked}>
    <View style={styles.lockedIcon}><Icon name={icon} size={20} color={colors.custom_softText} /></View>
    <View style={{ flex: 1, gap: 2 }}><T w="heavy" size={14.5}>{title}</T><T size={12.5} color={colors.muted}>{text}</T></View>
  </View>;
}
export const Later = ({ id }: { id: string }) => (
  <Locked id={id} testID={"a2-later-" + id} icon="clock-outline" title="Agle mock se shuru hoga"
    text="Is attempt mein har sawaal ka time record nahi hua tha. Agla mock doge to yeh hissa apne aap bhar jaayega." />
);

/** Set while a row of pills is being scrolled sideways, so that drag does not also change the analysis section. */
export const swipeGuard = { blocked: false };

/** Scrolling choice pills; the chosen one turns black like every other selector in the app. */
export function Pills({ id, value, onChange, items }: { id: string; value: string; onChange: (key: string) => void; items: [string, string][] }) {
  return <ScrollView testID={"a2-pills-" + id} horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pills} accessibilityRole="tablist"
    onScrollBeginDrag={() => { swipeGuard.blocked = true; }}>
    {items.map(([key, label]) => {
      const on = value === key;
      return <Press key={key} testID={`a2-pill-${id}-${slug(key)}`} accessibilityRole="tab" accessibilityState={{ selected: on }} onPress={() => onChange(key)} scaleTo={0.98}
        style={[styles.pill, on && styles.pillOn]}>
        <T size={12.5} w={on ? "heavy" : "bold"} color={on ? colors.onSurfaceInverse : colors.custom_softText}>{label}</T>
      </Press>;
    })}
  </ScrollView>;
}

export function Meter({ value, max = 100, tone = "brand", label, testID, height = 8 }: { value?: number | null; max?: number; tone?: Tone; label?: string; testID?: string; height?: number }) {
  const share = Math.max(0, Math.min(100, (100 * (value || 0)) / (max || 1)));
  return <View testID={testID} accessibilityRole="progressbar" accessibilityLabel={label || `${value ?? 0} / ${max}`} style={[styles.meter, { height, borderRadius: height / 2 }]}>
    <View style={{ width: `${share}%`, height: "100%", borderRadius: height / 2, backgroundColor: TONE[tone].fill }} />
  </View>;
}

export const Key = ({ items }: { items: [string, Tone][] }) => (
  <View style={styles.key}>{items.map(([label, tone]) => <View key={label} style={styles.keyItem}>
    <View style={[styles.keyDot, { backgroundColor: TONE[tone].fill }]} /><T size={11.5} color={colors.custom_softText}>{label}</T>
  </View>)}</View>
);

export function QChips({ id, ids, an, onOpen, max = 40 }: { id: string; ids: string[]; an: An; onOpen: Open; max?: number }) {
  const by = index(an), rows = ids.map(i => by[i]).filter(Boolean);
  if (!rows.length) return <T size={12.5} color={colors.muted}>Koi sawaal nahi.</T>;
  return <View testID={"a2-qchips-" + id} style={styles.qchips}>
    {rows.slice(0, max).map(q => {
      const t = TONE[OUT_TONE[q.outcome] || "mute"];
      return <Press key={q.id} testID={`a2-qchip-${id}-${q.number}`} onPress={() => onOpen(q.id)} accessibilityLabel={`Q${q.number}, ${q.subject}, ${RESULT[q.outcome]}. Solution kholo`}
        style={[styles.qchip, { backgroundColor: t.soft, borderColor: t.line }]}>
        <T size={12} w="heavy" color={t.ink}>Q{q.number}</T>
      </Press>;
    })}
    {rows.length > max ? <T size={12} w="bold" color={colors.muted} style={{ alignSelf: "center" }}>+{rows.length - max} aur</T> : null}
  </View>;
}

export const LinkButton = ({ label, onPress, testID, icon }: { label: string; onPress: () => void; testID?: string; icon?: IconName }) => (
  <Press testID={testID} onPress={onPress} accessibilityLabel={label} style={styles.link}>
    <T size={12.5} w="heavy" color={colors.brandText}>{label}</T>
    {icon ? <Icon name={icon} size={14} color={colors.brandText} /> : null}
  </Press>
);
export const Foot = ({ children, tone, testID }: { children: React.ReactNode; tone?: Tone; testID?: string }) => (
  <T testID={testID} size={12.5} color={tone ? TONE[tone].ink : colors.custom_softText}>{children}</T>
);
export const B = ({ children, tone }: { children: React.ReactNode; tone?: Tone }) => <T size={12.5} w="heavy" color={tone ? TONE[tone].ink : colors.onSurface}>{children}</T>;
export const EmptyLine = ({ children, testID }: { children: React.ReactNode; testID?: string }) => <T testID={testID} size={12.5} color={colors.muted}>{children}</T>;

/** A compact table that fits a phone: the first column takes the room, the rest are equal narrow columns. */
export function Grid({ head, rows, testID, first = 1.6 }: { head: React.ReactNode[]; rows: { key: string; cells: React.ReactNode[]; onPress?: () => void; testID?: string }[]; testID?: string; first?: number }) {
  const cell = (c: React.ReactNode, i: number, headRow = false) => (
    <View key={i} style={{ flex: i ? 1 : first, minWidth: 0, alignItems: i ? "center" : "flex-start", justifyContent: "center" }}>
      {typeof c === "string" || typeof c === "number"
        ? <T size={headRow ? 10 : 13} w={headRow ? "heavy" : i ? "bold" : "heavy"} color={headRow ? colors.custom_eyebrow : colors.onSurface} numberOfLines={headRow ? 2 : 1} style={headRow ? styles.gridHead : undefined}>{c}</T> : c}
    </View>
  );
  return <View testID={testID} style={styles.grid}>
    <View style={styles.gridRow}>{head.map((h, i) => cell(typeof h === "string" ? h.toUpperCase() : h, i, true))}</View>
    {rows.map(r => r.onPress
      ? <Press key={r.key} testID={r.testID} onPress={r.onPress} scaleTo={0.99} style={[styles.gridRow, styles.gridLine]}>{r.cells.map((c, i) => cell(c, i))}</Press>
      : <View key={r.key} testID={r.testID} style={[styles.gridRow, styles.gridLine]}>{r.cells.map((c, i) => cell(c, i))}</View>)}
  </View>;
}

/** A phone-sized stand-in for one row of a wide website table: title, a value on the right, a quiet line under it. */
export function StatRow({ testID, title, caption, right, rightTone, sub, onPress, tag, children, label }: {
  testID?: string; title: string; caption?: string; right?: React.ReactNode; rightTone?: Tone; sub?: string; onPress?: () => void; tag?: React.ReactNode; children?: React.ReactNode; label?: string;
}) {
  const body = <>
    <View style={styles.rowTop}>
      <View style={{ flex: 1, minWidth: 0 }}>
        <T w="heavy" size={14} numberOfLines={2}>{title}</T>
        {caption ? <T size={11.5} color={colors.muted}>{caption}</T> : null}
      </View>
      {tag}
      {typeof right === "string" || typeof right === "number" ? <T w="heavy" size={14.5} color={rightTone ? TONE[rightTone].ink : colors.onSurface}>{right}</T> : right}
      {onPress ? <Icon name="chevron-right" size={18} color={colors.custom_dim} /> : null}
    </View>
    {children}
    {sub ? <T size={12} color={colors.custom_softText}>{sub}</T> : null}
  </>;
  return onPress
    ? <Press testID={testID} onPress={onPress} scaleTo={0.99} accessibilityLabel={label || title} style={styles.statRow}>{body}</Press>
    : <View testID={testID} style={styles.statRow}>{body}</View>;
}

/** One question in a list: number, subject, result, time against Par and its tag. Opens the solution. */
export function QRow({ q, an, onPress, testID, extra }: { q: any; an: An; onPress: () => void; testID?: string; extra?: string }) {
  const tone = OUT_TONE[q.outcome] || "mute";
  return <Press testID={testID} onPress={onPress} scaleTo={0.99} accessibilityLabel={`Q${q.number}, ${q.subject}, ${RESULT[q.outcome]}. Solution kholo`} style={[styles.qrow, { borderLeftColor: TONE[tone].fill }]}>
    <T w="heavy" size={14} style={styles.qrowNo}>Q{q.number}</T>
    <View style={{ flex: 1, minWidth: 0, gap: 4 }}>
      <View style={styles.qrowTags}>
        <T size={12.5} w="bold" numberOfLines={1} style={{ flexShrink: 1 }}>{q.subject}</T>
        <ToneTag label={RESULT[q.outcome]} tone={tone} icon={OUT_ICON[q.outcome]} />
        {q.tag ? <TagChip tag={q.tag} copy={an.copy} /> : null}
      </View>
      <T size={11.5} color={colors.muted}>{extra ?? (q.time != null ? `Time ${mmss(q.time)}${q.par ? " · Par " + mmss(q.par) : ""}` : "Is sawaal ka time record nahi hua")}</T>
    </View>
    <Icon name="chevron-right" size={18} color={colors.custom_dim} />
  </Press>;
}

/** A small rounded button: a filter, a "Compare", a tag with its count. */
export const ChipButton = ({ testID, onPress, on, children, label }: { testID?: string; onPress: () => void; on?: boolean; children: React.ReactNode; label?: string }) => (
  <Press testID={testID} onPress={onPress} accessibilityLabel={label} accessibilityState={on === undefined ? undefined : { selected: on }} style={[styles.chipBtn, on && styles.chipBtnOn]}>{children}</Press>
);

/** Closed by default: tap the heading to read more (the rulebook, the full list). */
export function Fold({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  return <View testID={"a2-fold-" + id} style={styles.fold}>
    <Press testID={`a2-fold-${id}-toggle`} onPress={() => setOpen(!open)} accessibilityState={{ expanded: open }} scaleTo={0.99} style={styles.foldHead}>
      <T w="heavy" size={14} style={{ flex: 1 }}>{title}</T>
      <Icon name={open ? "chevron-up" : "chevron-down"} size={20} color={colors.custom_softText} />
    </Press>
    {open ? <View style={{ gap: space.md, paddingBottom: space.lg }}>{children}</View> : null}
  </View>;
}

/** A highlighted note with an icon: the Easy-marks leak, the guess rule. */
export function Callout({ testID, icon, tone, title, children }: { testID?: string; icon: IconName; tone: Tone; title: string; children: React.ReactNode }) {
  const t = TONE[tone];
  return <View testID={testID} style={[styles.callout, { borderColor: t.line, backgroundColor: t.soft }]}>
    <Icon name={icon} size={22} color={t.ink} />
    <View style={{ flex: 1, gap: 4 }}><T w="heavy" size={14.5}>{title}</T>{children}</View>
  </View>;
}

const styles = StyleSheet.create({
  rowTop: { flexDirection: "row", alignItems: "center", gap: 8 },
  statRow: { padding: space.md, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar, gap: 6 },
  qrow: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 56, paddingVertical: 8, paddingHorizontal: space.md, borderRadius: 14, borderWidth: 1, borderLeftWidth: 4, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar },
  qrowNo: { minWidth: 36 },
  qrowTags: { flexDirection: "row", alignItems: "center", flexWrap: "wrap", gap: 6 },
  chipBtn: { minHeight: 44, paddingHorizontal: 12, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, flexDirection: "row", alignItems: "center", gap: 6 },
  chipBtnOn: { borderColor: colors.onSurface, backgroundColor: colors.custom_cardRaised },
  fold: { borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, paddingHorizontal: space.lg },
  foldHead: { minHeight: 52, flexDirection: "row", alignItems: "center", gap: 8 },
  callout: { flexDirection: "row", gap: space.md, padding: space.lg, borderRadius: 20, borderWidth: 1 },
  block: { backgroundColor: colors.custom_card, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLine, padding: space.lg, gap: space.md },
  blockHead: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  kicker: { letterSpacing: 1.6 },
  tiles: { flexDirection: "row", flexWrap: "wrap", marginHorizontal: -4, rowGap: 8 },
  half: { width: "50%", paddingHorizontal: 4 }, third: { width: "33.333%", paddingHorizontal: 4 },
  tile: { flex: 1, minHeight: 84, padding: space.md, borderRadius: 18, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, gap: 2 },
  tileDot: { position: "absolute", top: 12, right: 12, width: 7, height: 7, borderRadius: 4 },
  tag: { flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, height: 22, borderRadius: 11, alignSelf: "flex-start", flexShrink: 1 },
  locked: { flexDirection: "row", gap: space.md, alignItems: "center", padding: space.lg, borderRadius: 22, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_cardRaised },
  lockedIcon: { width: 44, height: 44, borderRadius: 22, backgroundColor: colors.custom_card, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  pills: { gap: 8, paddingVertical: 2, paddingRight: space.lg },
  pill: { minHeight: 44, paddingHorizontal: 14, borderRadius: radius.pill, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_card, alignItems: "center", justifyContent: "center" },
  pillOn: { backgroundColor: colors.onSurface, borderColor: colors.onSurface },
  meter: { backgroundColor: colors.custom_qFresh, overflow: "hidden", flex: 1, minWidth: 30 },
  key: { flexDirection: "row", flexWrap: "wrap", columnGap: 14, rowGap: 4 },
  keyItem: { flexDirection: "row", alignItems: "center", gap: 6 },
  keyDot: { width: 9, height: 9, borderRadius: 3 },
  qchips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  qchip: { minWidth: 48, height: 44, paddingHorizontal: 8, borderRadius: 12, borderWidth: 1, alignItems: "center", justifyContent: "center" },
  link: { minHeight: 44, flexDirection: "row", alignItems: "center", gap: 4, alignSelf: "flex-start" },
  grid: { borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLine, backgroundColor: colors.custom_bar, paddingHorizontal: space.md },
  gridRow: { flexDirection: "row", alignItems: "center", minHeight: 44, gap: 6 },
  gridLine: { borderTopWidth: 1, borderTopColor: colors.custom_barLine },
  gridHead: { letterSpacing: 0.6, textAlign: "center" },
});
