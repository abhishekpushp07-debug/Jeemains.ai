import React, { useCallback, useMemo, useRef, useState } from "react";
import { FlatList, KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useReducedMotion } from "react-native-reanimated";
import { Icon, IconName, T, tap } from "@/src/components/ui";
import { arena, fonts, rapidSubjectColor as subjectColor } from "@/src/theme";
import { GoldTitle, RaisedButton } from "./arena";
import { Check } from "./parts";
import { CardCountPicker } from "./CardCount";
import { CardCount, CatalogSubject, PCM, Pick, SHORT, SUBJECTS, allTicked, cardCount, fitCount, getCardCount, isBitsat, picksToPlay, scopeLabel, setCardCount, tickAll, tickChapter, tickedOf } from "./scope";
import { classOf, useClassBook } from "@/src/classLevel";
import { useSearchTrack } from "@/src/searchTrack";

const ICON: Record<string, IconName> = { Physics: "atom", Chemistry: "flask-outline", Mathematics: "function-variant", English: "alphabetical-variant", "Logical Reasoning": "puzzle-outline" };
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
/** The first tab, and the one the picker opens on: the chapters of Physics, Chemistry and Maths in one list. */
const ALL_PCM = "PCM", PCM_NAMES = PCM.map((p) => p.subject), TABS = [ALL_PCM, ...SUBJECTS];
const firstTab = (picks: Pick[]) => (picks.length && !picks.some((p) => PCM_NAMES.includes(p.subject)) ? picks[0].subject : ALL_PCM);
const chaptersText = (n: number) => `${n} chapter${n === 1 ? "" : "s"}`;
/** Rapid Fire's Physics, Chemistry and Maths chapters are the JEE ones: that list says which class each belongs to. */
const CLASS_EXAM = "jee-main";
/** One line of the list: a heading (no `name`; `label` = its words) or one chapter. */
type Line = { key: string; subject: string; name?: string; count: number; label?: string };

/** One chapter with its tick. Kept apart so that a tick redraws that one row, not the whole list. */
const ChapterRow = React.memo(function ChapterRow({ subject, name, count, on, tag, onToggle }: { subject: string; name: string; count: number; on: boolean; tag: boolean; onToggle: (subject: string, name: string) => void }) {
  const tint = subjectColor(subject);
  return <Pressable testID={`rf-scope-chapter-${slug(name)}`} disabled={!count} accessibilityRole="checkbox" accessibilityState={{ checked: on, disabled: !count }} aria-checked={on}
    onPress={() => { tap(); onToggle(subject, name); }} style={[styles.row, on && { borderColor: tint, backgroundColor: arena.panelHi }, !count && styles.off]}>
    <View style={[styles.bar, { backgroundColor: tint }]} />
    <View style={styles.flex}>
      <T w="bold" size={15} color={arena.text} numberOfLines={2}>{name}</T>
      <T size={11} color={arena.muted}>{!count ? "Cards coming soon" : tag ? `${SHORT[subject]} · ${count} cards` : `${count} cards`}</T>
    </View>
    <Check on={on} />
  </Pressable>;
});

/**
 * Battleground picker. Nothing is ever ticked for the student: the picker opens on the PCM tab with every chapter unticked.
 * Tabs: PCM, then each subject. Under them "Select all" and "Clear" for the tab in view, then that tab's chapters:
 * for Physics, Chemistry and Maths the Class 11 chapters first, then the Class 12 ones, each under a small heading.
 * Any number of chapters may be ticked, across subjects; a ticked chapter is unticked with one tap, also after Select all.
 */
export function ScopeSheet({ visible, onClose, subjects, value, onDone, onPlay, min = 30, title = "Choose your battleground", hint, action, testID = "rf-scope-sheet" }: {
  visible: boolean; onClose: () => void; subjects: CatalogSubject[]; value: Pick[]; onDone: (picks: Pick[]) => void; min?: number; title?: string; hint?: string; action?: string; testID?: string;
  /** Lobby: PLAY right here starts a Quick Match on what is picked (saved as the lobby's choice too). */
  onPlay?: (picks: Pick[]) => void;
}) {
  const insets = useSafeAreaInsets(), reduced = useReducedMotion(), list = useRef<FlatList<Line>>(null);
  const [draft, setDraft] = useState<Pick[]>(value), [tab, setTab] = useState(firstTab(value));
  const [q, setQ] = useState("");
  const [was, setWas] = useState(false), [count, setCount] = useState<CardCount>(getCardCount()); // the 30/50/100 choice is kept on SAVE / PLAY only
  if (visible !== was) { setWas(visible); if (visible) { setDraft(value); setTab(firstTab(value)); setQ(""); setCount(getCardCount()); } }
  const query = q.trim().toLowerCase(), book = useClassBook();
  // The subjects of the tab in view, and the lines under it (with a search: the chapters of every subject that match).
  const shown = useMemo(() => subjects.filter((s) => (tab === ALL_PCM ? PCM_NAMES.includes(s.name) : s.name === tab)), [subjects, tab]);
  const lines = useMemo<Line[]>(() => {
    const chapters = (s: CatalogSubject) => s.chapters.map((c) => ({ key: `${s.name}:${c.name}`, subject: s.name, name: c.name, count: c.count }));
    if (query) return subjects.flatMap((s) => chapters(s).filter((c) => c.name.toLowerCase().includes(query)));
    const all = shown.flatMap(chapters), levels = all.map((c) => classOf(CLASS_EXAM, c.subject, c.name));
    // A tab whose chapters have no class (English, Reasoning): each subject under its own heading, as it comes.
    if (!levels.some((level) => level !== null)) return shown.flatMap((s) => [{ key: s.name, subject: s.name, count: s.chapters.length, label: `${SHORT[s.name].toUpperCase()} · ${s.chapters.length} CHAPTERS${isBitsat(s.name) ? " · BITSAT 2026" : ""}` }, ...chapters(s)]);
    // Physics, Chemistry, Maths: Class 11 first, then Class 12; a chapter whose class is not known comes last. Only the order
    // and the two headings: every tick, Select all and Clear work on the whole tab exactly as before.
    const where = tab === ALL_PCM ? "PCM" : SHORT[tab].toUpperCase();
    return ([11, 12, null] as const).flatMap((level) => {
      const part = all.filter((_, i) => levels[i] === level);
      return part.length ? [{ key: `class:${level}`, subject: "", count: part.length, label: `${level ? `CLASS ${level}` : "MORE"} · ${where} · ${part.length} CHAPTERS` }, ...part] : [];
    });
  }, [query, subjects, shown, tab, book]); // eslint-disable-line react-hooks/exhaustive-deps
  useSearchTrack("rapid_chapters", query, subjects.length ? lines.length : null);
  const ticked = useMemo(() => new Set(subjects.flatMap((s) => tickedOf(draft, s).map((c) => `${s.name}:${c}`))), [draft, subjects]);
  // What SAVE / PLAY hands over: see picksToPlay (whole subjects share evenly; with single chapters, every ticked chapter does).
  const out = useMemo(() => picksToPlay(draft, subjects), [draft, subjects]);
  const cards = cardCount(out, subjects), size = fitCount(count, cards), some = draft.length > 0;
  const all = shown.length > 0 && shown.every((s) => allTicked(draft, s)), any = shown.some((s) => tickedOf(draft, s).length > 0);
  const done = () => { setCardCount(count); onDone(out); onClose(); return out; };
  const toggle = useCallback((subject: string, name: string) => { const s = subjects.find((x) => x.name === subject); if (s) setDraft((d) => tickChapter(d, s, name)); }, [subjects]);
  const open = (t: string) => { tap(); setTab(t); list.current?.scrollToOffset({ offset: 0, animated: false }); };
  // On the PCM tab the three subjects' chapters stand together under each class, so every row says its subject.
  const tagged = !!query || tab === ALL_PCM;
  const line = useCallback(({ item }: { item: Line }) => (item.name === undefined
    ? <T testID={`rf-scope-head-${slug(item.key)}`} w="heavy" size={11} color={arena.muted} style={styles.label}>{item.label}</T>
    : <ChapterRow subject={item.subject} name={item.name} count={item.count} on={ticked.has(item.key)} tag={tagged} onToggle={toggle} />), [ticked, tagged, toggle]);

  // Above the chapters of a tab: the round's size, then Select all and Clear for exactly the chapters listed below.
  const head = <View style={styles.top}>
    <CardCountPicker available={some ? cards : undefined} value={count} onChange={setCount} testID="rf-scope-count" />
    <View style={styles.bulk}>
      <Pressable testID="rf-scope-select-all" accessibilityRole="checkbox" accessibilityState={{ checked: all }} aria-checked={all} accessibilityLabel={`Select all chapters of ${tab === ALL_PCM ? "Physics, Chemistry and Maths" : SHORT[tab]}`}
        onPress={() => { tap(); setDraft((d) => tickAll(d, shown, !all)); }} style={[styles.bulkKey, styles.flex, all && styles.bulkOn]}>
        <Check on={all} />
        <View style={styles.flex}>
          <T w="heavy" size={14} color={arena.text} numberOfLines={1}>{all ? "All selected" : "Select all"}</T>
          <T w="bold" size={11} color={arena.muted} numberOfLines={1}>{`${tab === ALL_PCM ? "PCM" : SHORT[tab]} · ${chaptersText(shown.reduce((n, s) => n + s.chapters.length, 0))}`}</T>
        </View>
      </Pressable>
      <Pressable testID="rf-scope-clear-all" disabled={!any} accessibilityRole="button" accessibilityState={{ disabled: !any }} accessibilityLabel={`Clear ${tab === ALL_PCM ? "Physics, Chemistry and Maths" : SHORT[tab]}`}
        onPress={() => { tap(); setDraft((d) => tickAll(d, shown, false)); }} style={[styles.bulkKey, styles.clear, !any && styles.off]}>
        <Icon name="close" size={16} color={arena.text} />
        <T w="heavy" size={13} color={arena.text}>Clear</T>
      </Pressable>
    </View>
  </View>;

  return <Modal visible={visible} transparent animationType={reduced ? "none" : "slide"} onRequestClose={onClose} statusBarTranslucent>
    <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={styles.flex}>
      <Pressable testID={`${testID}-backdrop`} onPress={onClose} style={styles.backdrop} accessibilityLabel="Close picker" />
      <View testID={testID} style={[styles.sheet, { paddingBottom: insets.bottom + 12 }]}>
        <View style={styles.handle} />
        <View style={styles.head}>
          <View style={styles.flex}>
            <GoldTitle size={20} testID={`${testID}-title`}>{title}</GoldTitle>
            <T w="bold" size={12} color={arena.aqua}>{hint || "Any subjects, any chapters"}</T>
          </View>
          <Pressable testID={`${testID}-close`} onPress={onClose} accessibilityLabel="Close" style={styles.close}><Icon name="close" size={24} color={arena.muted} /></Pressable>
        </View>
        <View style={[styles.search, q ? styles.searchOn : null]}>
          <Icon name="magnify" size={20} color={q ? arena.aqua : arena.muted} />
          <TextInput testID="rf-scope-search" value={q} onChangeText={setQ} placeholder="Search chapters…" placeholderTextColor={arena.faint} style={styles.input} />
          {q ? <Pressable testID="rf-scope-clear" onPress={() => setQ("")} accessibilityLabel="Clear search" style={styles.close}><Icon name="close-circle" size={18} color={arena.muted} /></Pressable> : null}
        </View>

        {query ? null : <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabBar} contentContainerStyle={styles.tabs} testID="rf-scope-tabs">
          {TABS.map((t) => {
            const on = tab === t, tint = t === ALL_PCM ? arena.gold : subjectColor(t);
            const n = subjects.reduce((k, s) => k + ((t === ALL_PCM ? PCM_NAMES.includes(s.name) : s.name === t) ? tickedOf(draft, s).length : 0), 0);
            return <Pressable key={t} testID={`rf-scope-tab-${slug(t)}`} accessibilityRole="tab" accessibilityState={{ selected: on }} aria-selected={on} onPress={() => open(t)} style={[styles.tab, on && { backgroundColor: tint }]}>
              <Icon name={t === ALL_PCM ? "shuffle-variant" : ICON[t]} size={15} color={on ? arena.badgeInk : arena.muted} />
              <T w="heavy" size={12} color={on ? arena.badgeInk : arena.muted}>{t === ALL_PCM ? "PCM" : SHORT[t]}</T>
              {n ? <View style={[styles.count, { backgroundColor: on ? arena.badgeInk : tint }]}><T w="heavy" size={10} color={on ? arena.text : arena.badgeInk}>{n}</T></View> : null}
            </Pressable>;
          })}
        </ScrollView>}

        <FlatList ref={list} data={lines} keyExtractor={(x) => x.key} renderItem={line} ListHeaderComponent={query ? undefined : head} keyboardShouldPersistTaps="handled"
          contentContainerStyle={styles.body} showsVerticalScrollIndicator={false} initialNumToRender={12} windowSize={9}
          ListEmptyComponent={<T testID="rf-scope-none" size={14} color={arena.muted} style={styles.center}>{query ? `No chapter matches “${q}”.` : subjects.length ? "No chapters here yet." : "Loading chapters…"}</T>} />

        <View style={styles.tray} testID="rf-scope-tray">
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.trayRow}>
            {subjects.map((s) => {
              const n = tickedOf(draft, s).length;
              return n ? <Pressable key={s.name} testID={`rf-scope-picked-${slug(s.name)}`} accessibilityLabel={`Clear ${SHORT[s.name]}`}
                onPress={() => { tap(); setDraft((d) => tickAll(d, [s], false)); }} style={[styles.picked, { borderColor: subjectColor(s.name) }]}>
                <T w="heavy" size={12} color={arena.text} numberOfLines={1} style={styles.pickedText}>{`${SHORT[s.name]} · ${allTicked(draft, s) ? "all" : n}`}</T>
                <Icon name="close" size={14} color={arena.muted} />
              </Pressable> : null;
            })}
            {!some ? <T testID="rf-scope-empty" size={12} color={arena.muted}>Nothing picked yet</T> : null}
          </ScrollView>
          {some && cards < min ? <T testID="rf-scope-short" w="bold" size={12} color={arena.danger} style={styles.center}>{cards} cards. Add a chapter for a full {min}-card round.</T> : null}
          {onPlay ? <View style={styles.playRow}>
            <RaisedButton testID="rf-scope-done" height={58} tone="wine" label="SAVE" sub={some ? chaptersText(ticked.size) : "Nothing picked"} disabled={!some || cards < min} onPress={done} style={styles.save} />
            <RaisedButton testID="rf-scope-play" height={58} streak icon="swords" label="PLAY" sub={!some ? "Tick chapters first" : `Quick Match · ${size} cards`}
              disabled={!some || cards < min || !size} onPress={() => onPlay(done())} style={styles.play} />
          </View> : <RaisedButton testID="rf-scope-done" height={58} streak icon={action ? "flame" : undefined} label={action || (some ? scopeLabel(out).toUpperCase() : "PICK CHAPTERS")}
            sub={some ? `${action ? scopeLabel(out) + " · " : ""}${chaptersText(ticked.size)} · ${cards} cards` : "Tick chapters, or tap Select all"}
            disabled={!some || cards < min} onPress={done} />}
        </View>
      </View>
    </KeyboardAvoidingView>
  </Modal>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, label: { letterSpacing: 1.5, marginTop: 4 },
  backdrop: { flex: 1, backgroundColor: arena.scrim },
  sheet: { height: "90%", backgroundColor: arena.panel, borderTopLeftRadius: 28, borderTopRightRadius: 28, borderTopWidth: 1.5, borderColor: arena.rim, paddingTop: 8, gap: 10 },
  handle: { alignSelf: "center", width: 44, height: 5, borderRadius: 3, backgroundColor: arena.rim },
  head: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 18 },
  close: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  search: { flexDirection: "row", alignItems: "center", gap: 8, height: 50, marginHorizontal: 18, paddingLeft: 14, borderRadius: 16, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  searchOn: { borderColor: arena.aqua },
  input: { flex: 1, color: arena.text, fontFamily: fonts.bold, fontSize: 16 },
  body: { paddingHorizontal: 18, paddingBottom: 12, gap: 8 },
  top: { gap: 8 },
  // Select all and Clear: two keys side by side, each tall enough for a thumb.
  bulk: { flexDirection: "row", gap: 8 },
  bulkKey: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 52, paddingHorizontal: 12, borderRadius: 16, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  bulkOn: { borderColor: arena.gold, backgroundColor: arena.panelHi }, clear: { gap: 6, paddingHorizontal: 16 },
  tabBar: { flexGrow: 0, flexShrink: 0 }, tabs: { flexDirection: "row", gap: 6, paddingHorizontal: 18 },
  tab: { height: 44, paddingHorizontal: 14, borderRadius: 22, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4, backgroundColor: arena.panelHi },
  count: { minWidth: 18, height: 18, borderRadius: 9, paddingHorizontal: 4, alignItems: "center", justifyContent: "center" },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 58, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  off: { opacity: 0.45 }, bar: { width: 5, height: 30, borderRadius: 3 },
  tray: { paddingHorizontal: 18, paddingTop: 10, gap: 8, borderTopWidth: 1, borderTopColor: arena.rim },
  trayRow: { gap: 6, alignItems: "center", minHeight: 36 },
  picked: { flexDirection: "row", alignItems: "center", gap: 4, height: 34, paddingHorizontal: 10, borderRadius: 17, borderWidth: 1.5, backgroundColor: arena.panelHi, maxWidth: 220 },
  pickedText: { flexShrink: 1 }, playRow: { flexDirection: "row", gap: 10 }, save: { flex: 1 }, play: { flex: 1.7 },
});
