import React, { useMemo, useState } from "react";
import { KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, TextInput, View, useWindowDimensions } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { useReducedMotion } from "react-native-reanimated";
import { Icon, IconName, T, tap } from "@/src/components/ui";
import { arena, fonts, rapidSubjectColor as subjectColor } from "@/src/theme";
import { GoldTitle, RaisedButton } from "./arena";
import { Check } from "./parts";
import { CardCountPicker } from "./CardCount";
import { CardCount, CatalogSubject, MAX_PICKS, PCM, Pick, SHORT, SUBJECTS, cardCount, fitCount, getCardCount, isBitsat, isPCM, isWhole, normalise, pickKey, scopeLabel, setCardCount } from "./scope";

const ICON: Record<string, IconName> = { Physics: "atom", Chemistry: "flask-outline", Mathematics: "function-variant", English: "alphabetical-variant", "Logical Reasoning": "puzzle-outline" };
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const PCM_SUBJECTS = SUBJECTS.slice(0, 3), BITSAT_ROW = SUBJECTS.slice(3);

/** Toggle one pick in a list, keeping the 5-pick limit. Returns null when the limit stops it. */
export function togglePick(picks: Pick[], pick: Pick): Pick[] | null {
  const key = pickKey({ ...pick, chapter: pick.chapter || null });
  if (picks.some((p) => pickKey(p) === key)) return picks.filter((p) => pickKey(p) !== key);
  // A whole subject replaces that subject's chapters.
  const rest = pick.chapter ? picks : picks.filter((p) => p.subject !== pick.subject);
  return rest.length >= MAX_PICKS ? null : normalise([...rest, pick]);
}

/** The subjects (and PCM) right on the stage: one tap adds or removes a whole subject. BITSAT English and Reasoning sit on a second row. */
export function SubjectChips({ picks, onChange, onLimit, testID = "rf-subject-chips" }: { picks: Pick[]; onChange: (p: Pick[]) => void; onLimit?: () => void; testID?: string }) {
  const pcm = isPCM(picks), roomy = useWindowDimensions().width >= 380;
  const chip = (s: string) => {
    const whole = isWhole(picks, s), chapters = picks.filter((p) => p.subject === s && p.chapter).length;
    const on = whole || chapters > 0, tint = subjectColor(s);
    return <Pressable key={s} testID={`${testID}-${slug(s)}`} accessibilityRole="checkbox" accessibilityState={{ checked: on }} aria-checked={on} accessibilityLabel={`${isBitsat(s) ? "BITSAT " : ""}${SHORT[s]}${chapters ? `, ${chapters} chapters` : ""}`}
      onPress={() => { tap(); const next = whole ? picks.filter((p) => p.subject !== s) : togglePick(picks, { subject: s, chapter: null }); if (!next) onLimit?.(); else if (next.length) onChange(next); }}
      style={[styles.chip, styles.chipFlex, on && { borderColor: tint, backgroundColor: arena.panelHi }]}>
      {roomy || isBitsat(s) ? <Icon name={ICON[s]} size={14} color={on ? tint : arena.faint} /> : null}
      <T w="heavy" size={roomy ? 12 : 11.5} color={on ? arena.text : arena.muted} numberOfLines={1} style={styles.shrink}>{SHORT[s]}</T>
      {chapters && !whole ? <View style={[styles.count, { backgroundColor: tint }]}><T w="heavy" size={10} color={arena.badgeInk}>{chapters}</T></View> : null}
      {on ? <View style={[styles.lit, { backgroundColor: tint }]} /> : null}
    </Pressable>;
  };
  return <View testID={testID} style={styles.chipRows}>
    <View style={styles.chips}>
      {PCM_SUBJECTS.map(chip)}
      <Pressable testID={`${testID}-pcm`} accessibilityRole="checkbox" accessibilityState={{ checked: pcm }} aria-checked={pcm} accessibilityLabel="PCM Mixed, all three subjects" onPress={() => { tap(); onChange(PCM); }} style={[styles.chip, styles.pcm, !roomy && styles.pcmNarrow, pcm && styles.pcmOn]}>
        {roomy ? <Icon name="shuffle-variant" size={14} color={pcm ? arena.badgeInk : arena.gold} /> : null}
        <T w="heavy" size={12} color={pcm ? arena.badgeInk : arena.gold}>PCM</T>
      </Pressable>
    </View>
    <View style={styles.chips}>
      <View style={styles.bitsat} accessibilityElementsHidden importantForAccessibility="no"><T w="heavy" size={10} color={arena.gold} style={styles.bitsatText}>BITSAT</T></View>
      {BITSAT_ROW.map(chip)}
    </View>
  </View>;
}

/**
 * Battleground picker: up to 5 picks across Physics, Chemistry and Maths. Each pick is a whole subject (Mixed) or one chapter.
 * Quick mixes on top (PCM Mixed and Mixed of each subject), chapters per subject below, chosen picks in the tray.
 */
export function ScopeSheet({ visible, onClose, subjects, value, onDone, onPlay, min = 30, title = "Choose your battleground", hint, action, testID = "rf-scope-sheet" }: {
  visible: boolean; onClose: () => void; subjects: CatalogSubject[]; value: Pick[]; onDone: (picks: Pick[]) => void; min?: number; title?: string; hint?: string; action?: string; testID?: string;
  /** Lobby: PLAY right here starts a Quick Match on what is picked (saved as the lobby's choice too). */
  onPlay?: (picks: Pick[]) => void;
}) {
  const insets = useSafeAreaInsets(), reduced = useReducedMotion();
  const [draft, setDraft] = useState<Pick[]>(value), [tab, setTab] = useState(value[0]?.subject || "Physics");
  const [q, setQ] = useState(""), [warn, setWarn] = useState("");
  const [was, setWas] = useState(false), [count, setCount] = useState<CardCount>(getCardCount()); // the 30/50/100 choice is kept on SAVE / PLAY only
  if (visible !== was) { setWas(visible); if (visible) { setDraft(value); setTab(value[0]?.subject || "Physics"); setQ(""); setWarn(""); setCount(getCardCount()); } }
  const query = q.trim().toLowerCase();
  const hits = useMemo(() => (query ? subjects.flatMap((s) => s.chapters.filter((c) => c.name.toLowerCase().includes(query)).map((c) => ({ ...c, subject: s.name }))) : []), [query, subjects]);
  const cards = cardCount(draft, subjects), full = draft.length >= MAX_PICKS, size = fitCount(count, cards);
  const save = () => { setCardCount(count); onDone(draft); onClose(); };
  const cur = subjects.find((s) => s.name === tab);

  const toggle = (pick: Pick) => {
    const next = togglePick(draft, pick);
    if (!next) { setWarn(`Up to ${MAX_PICKS} picks. Remove one to add another.`); return; }
    setWarn(""); setDraft(next);
  };

  const mix = (label: string, sub: string, on: boolean, onPress: () => void, testId: string, colors: [string, string], icon: IconName) =>
    <Pressable key={testId} testID={testId} accessibilityRole="checkbox" accessibilityState={{ checked: on }} aria-checked={on} accessibilityLabel={label} onPress={() => { tap(); onPress(); }} style={[styles.mix, on && styles.mixOn]}>
      <LinearGradient colors={colors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.mixFace}>
        <View style={styles.mixGloss} />
        <Icon name={icon} size={22} color={arena.text} />
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{label}</T>
          <T w="bold" size={10.5} color={arena.text} numberOfLines={1} style={styles.dim}>{sub}</T>
        </View>
      </LinearGradient>
      {on ? <View style={styles.tick}><Icon name="check-bold" size={13} color={arena.badgeInk} /></View> : null}
    </Pressable>;

  const row = (s: string, c: { name: string; count: number }) => {
    const whole = isWhole(draft, s), on = whole || draft.some((p) => p.subject === s && p.chapter === c.name);
    const tint = subjectColor(s);
    return <Pressable key={s + c.name} testID={`rf-scope-chapter-${slug(c.name)}`} disabled={whole || !c.count} accessibilityRole="checkbox" accessibilityState={{ checked: on, disabled: whole }} aria-checked={on}
      onPress={() => { tap(); toggle({ subject: s, chapter: c.name }); }} style={[styles.row, on && { borderColor: tint, backgroundColor: arena.panelHi }, (!c.count || (!on && full)) && styles.off]}>
      <View style={[styles.bar, { backgroundColor: tint }]} />
      <View style={styles.flex}>
        <T w="bold" size={15} color={arena.text} numberOfLines={2}>{c.name}</T>
        <T size={11} color={arena.muted}>{whole ? `In Mixed ${SHORT[s]}` : !c.count ? "Cards coming soon" : query ? `${SHORT[s]} · ${c.count} cards` : `${c.count} cards`}</T>
      </View>
      <Check on={on} />
    </Pressable>;
  };

  return <Modal visible={visible} transparent animationType={reduced ? "none" : "slide"} onRequestClose={onClose} statusBarTranslucent>
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.flex}>
      <Pressable testID={`${testID}-backdrop`} onPress={onClose} style={styles.backdrop} accessibilityLabel="Close picker" />
      <View testID={testID} style={[styles.sheet, { paddingBottom: insets.bottom + 12 }]}>
        <View style={styles.handle} />
        <View style={styles.head}>
          <View style={styles.flex}>
            <GoldTitle size={20} testID={`${testID}-title`}>{title}</GoldTitle>
            <T w="bold" size={12} color={arena.aqua}>{hint || `Up to ${MAX_PICKS} · mix subjects and chapters`}</T>
          </View>
          <Pressable testID={`${testID}-close`} onPress={onClose} accessibilityLabel="Close" style={styles.close}><Icon name="close" size={24} color={arena.muted} /></Pressable>
        </View>
        <View style={[styles.search, q ? styles.searchOn : null]}>
          <Icon name="magnify" size={20} color={q ? arena.aqua : arena.muted} />
          <TextInput testID="rf-scope-search" value={q} onChangeText={setQ} placeholder="Search chapters…" placeholderTextColor={arena.faint} style={styles.input} />
          {q ? <Pressable testID="rf-scope-clear" onPress={() => setQ("")} accessibilityLabel="Clear search" style={styles.close}><Icon name="close-circle" size={18} color={arena.muted} /></Pressable> : null}
        </View>

        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
          {query ? (hits.length ? hits.map((c) => row(c.subject, c)) : <T size={14} color={arena.muted} style={styles.center}>No chapter matches “{q}”.</T>) : <>
            <T w="heavy" size={11} color={arena.muted} style={styles.label}>QUICK MIX</T>
            <View style={styles.mixes}>
              {mix("PCM Mixed", "All 3 subjects", isPCM(draft), () => { setWarn(""); setDraft(PCM); }, "rf-scope-pcm", [arena.goldDeep, "#7A1F12"], "shuffle-variant")}
              {SUBJECTS.map((s) => mix(SHORT[s], `${isBitsat(s) ? "BITSAT · " : "Mixed · "}${subjects.find((x) => x.name === s)?.total ?? 0} cards`, isWhole(draft, s),
                () => toggle({ subject: s, chapter: null }), `rf-scope-mixed-${slug(s)}`, [subjectColor(s) + "CC", arena.panelEdge], ICON[s]))}
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabs} testID="rf-scope-tabs">
              {SUBJECTS.map((s) => {
                const on = tab === s, n = draft.filter((p) => p.subject === s).length;
                return <Pressable key={s} testID={`rf-scope-tab-${slug(s)}`} accessibilityRole="tab" accessibilityState={{ selected: on }} onPress={() => { tap(); setTab(s); }} style={[styles.tab, on && { backgroundColor: subjectColor(s) }]}>
                  <Icon name={ICON[s]} size={15} color={on ? arena.badgeInk : arena.muted} />
                  <T w="heavy" size={12} color={on ? arena.badgeInk : arena.muted}>{SHORT[s]}</T>
                  {n ? <View style={[styles.count, { backgroundColor: on ? arena.badgeInk : subjectColor(s) }]}><T w="heavy" size={10} color={on ? arena.text : arena.badgeInk}>{n}</T></View> : null}
                </Pressable>;
              })}
            </ScrollView>
            <CardCountPicker available={draft.length ? cards : undefined} value={count} onChange={setCount} testID="rf-scope-count" />
            <T w="heavy" size={11} color={arena.muted} style={styles.label}>{(cur?.chapters.length ?? 0) + " CHAPTERS" + (isBitsat(tab) ? " · BITSAT 2026" : "")}</T>
            {(cur?.chapters || []).map((c) => row(tab, c))}
          </>}
        </ScrollView>

        <View style={styles.tray} testID="rf-scope-tray">
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.trayRow}>
            {draft.map((p) => <Pressable key={pickKey(p)} testID={`rf-scope-picked-${slug(p.chapter || "mixed-" + p.subject)}`} accessibilityLabel={`Remove ${p.chapter || "Mixed " + SHORT[p.subject]}`}
              onPress={() => { tap(); setWarn(""); setDraft(draft.filter((x) => pickKey(x) !== pickKey(p))); }} style={[styles.picked, { borderColor: subjectColor(p.subject) }]}>
              <T w="heavy" size={12} color={arena.text} numberOfLines={1} style={styles.pickedText}>{p.chapter || `Mixed ${SHORT[p.subject]}`}</T>
              <Icon name="close" size={14} color={arena.muted} />
            </Pressable>)}
            {!draft.length ? <T size={12} color={arena.muted}>Nothing picked yet</T> : null}
          </ScrollView>
          {warn ? <T testID="rf-scope-warn" w="bold" size={12} color={arena.danger} style={styles.center}>{warn}</T>
            : draft.length && cards < min ? <T testID="rf-scope-short" w="bold" size={12} color={arena.danger} style={styles.center}>{cards} cards. Add a chapter for a full {min}-card round.</T> : null}
          {onPlay ? <View style={styles.playRow}>
            <RaisedButton testID="rf-scope-done" height={58} tone="wine" label="SAVE" sub={`${draft.length}/${MAX_PICKS} picked`} disabled={!draft.length || cards < min} onPress={save} style={styles.save} />
            <RaisedButton testID="rf-scope-play" height={58} streak icon="swords" label="PLAY" sub={!draft.length ? "Pick a subject" : `Quick Match · ${size} cards`}
              disabled={!draft.length || cards < min || !size} onPress={() => { save(); onPlay(draft); }} style={styles.play} />
          </View> : <RaisedButton testID="rf-scope-done" height={58} streak icon={action ? "flame" : undefined} label={!draft.length ? "PICK A SUBJECT" : action || scopeLabel(draft).toUpperCase()}
            sub={`${action && draft.length ? scopeLabel(draft) + " · " : ""}${draft.length}/${MAX_PICKS} picked · ${cards} cards`}
            disabled={!draft.length || cards < min} onPress={save} />}
        </View>
      </View>
    </KeyboardAvoidingView>
  </Modal>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, dim: { opacity: 0.85 }, label: { letterSpacing: 1.5, marginTop: 4 },
  backdrop: { flex: 1, backgroundColor: arena.scrim },
  sheet: { height: "90%", backgroundColor: arena.panel, borderTopLeftRadius: 28, borderTopRightRadius: 28, borderTopWidth: 1.5, borderColor: arena.rim, paddingTop: 8, gap: 10 },
  handle: { alignSelf: "center", width: 44, height: 5, borderRadius: 3, backgroundColor: arena.rim },
  head: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 18 },
  close: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  search: { flexDirection: "row", alignItems: "center", gap: 8, height: 50, marginHorizontal: 18, paddingLeft: 14, borderRadius: 16, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  searchOn: { borderColor: arena.aqua },
  input: { flex: 1, color: arena.text, fontFamily: fonts.bold, fontSize: 16 },
  body: { paddingHorizontal: 18, paddingBottom: 12, gap: 8 },
  mixes: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  mix: { width: "48.6%", borderRadius: 16, borderWidth: 2, borderColor: "transparent" }, mixOn: { borderColor: arena.gold },
  mixFace: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 60, paddingHorizontal: 10, borderRadius: 14, overflow: "hidden" },
  mixGloss: { position: "absolute", top: 0, left: 0, right: 0, height: "45%", backgroundColor: arena.panelGloss },
  tabs: { flexDirection: "row", gap: 6, marginTop: 6, paddingRight: 4 },
  tab: { height: 44, paddingHorizontal: 14, borderRadius: 22, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4, backgroundColor: arena.panelHi },
  count: { minWidth: 18, height: 18, borderRadius: 9, paddingHorizontal: 4, alignItems: "center", justifyContent: "center" },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  off: { opacity: 0.45 }, bar: { width: 5, height: 30, borderRadius: 3 },
  tray: { paddingHorizontal: 18, paddingTop: 10, gap: 8, borderTopWidth: 1, borderTopColor: arena.rim },
  trayRow: { gap: 6, alignItems: "center", minHeight: 36 },
  picked: { flexDirection: "row", alignItems: "center", gap: 4, height: 34, paddingHorizontal: 10, borderRadius: 17, borderWidth: 1.5, backgroundColor: arena.panelHi, maxWidth: 220 },
  pickedText: { flexShrink: 1 }, playRow: { flexDirection: "row", gap: 10 }, save: { flex: 1 }, play: { flex: 1.7 },
  chips: { flexDirection: "row", gap: 6, alignSelf: "stretch", justifyContent: "center" },
  chipRows: { alignSelf: "stretch", gap: 6 },
  bitsat: { minHeight: 44, paddingHorizontal: 8, borderRadius: 12, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: arena.goldDeep, borderStyle: "dashed" },
  bitsatText: { letterSpacing: 1 },
  chip: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4, minHeight: 44, paddingHorizontal: 9, borderRadius: 22, borderWidth: 1.5, borderColor: arena.rim, backgroundColor: arena.panelEdge, overflow: "hidden" },
  chipFlex: { flex: 1, minWidth: 0, paddingHorizontal: 5 }, shrink: { flexShrink: 1 }, pcmNarrow: { paddingHorizontal: 8 },
  lit: { position: "absolute", bottom: 0, left: "25%", right: "25%", height: 3, borderTopLeftRadius: 3, borderTopRightRadius: 3 },
  tick: { position: "absolute", top: -4, right: -4, width: 22, height: 22, borderRadius: 11, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold, borderWidth: 1.5, borderColor: arena.goldDeep },
  pcm: { borderColor: arena.goldDeep }, pcmOn: { backgroundColor: arena.gold, borderColor: arena.goldDeep },
});
