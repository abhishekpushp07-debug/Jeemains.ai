import React, { useMemo, useState } from "react";
import { ActivityIndicator, Modal, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useReducedMotion } from "react-native-reanimated";
import { ErrorBox, Icon, T, tap } from "@/src/components/ui";
import { arena, rapidSubjectColor as subjectColor } from "@/src/theme";
import { GoldTitle, RaisedButton, Segment } from "./arena";
import { Note } from "./parts";
import { CARD_SECONDS, SHORT, SUBJECTS, useCardCount } from "./scope";
import { WeakTopics, useSprintStart } from "./WeakSprint";

// The Weak cards sheet, in two clear parts.
// Chapters: every chapter with cards still missed, under its subject; subject tabs jump straight to one subject; REPLAY deals that chapter's misses.
// Topic Sprint: the subtopics the student keeps missing, under their subject, and one START button for a sprint dealt only from them.
export type WeakChapter = { subject: string; chapter: string; misses: number; remaining: number };
export type WeakChapters = { items: WeakChapter[]; remaining: number };
type Query<T> = { data: T | null; error: string; loading: boolean; reload: () => void };
type Part = "chapters" | "topics";

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const plural = (n: number, one: string) => `${n} ${one}${n === 1 ? "" : one.endsWith("s") ? "es" : "s"}`;
const short = (s: string) => SHORT[s] || s;
const rank = (s: string) => { const i = (SUBJECTS as readonly string[]).indexOf(s); return i < 0 ? SUBJECTS.length : i; };

/** Rows under their subject, subjects in the arena's usual order. `start` is the first row's place in the whole list. */
function sections<T extends { subject: string }>(rows: T[]) {
  const map = new Map<string, T[]>();
  for (const r of rows) map.set(r.subject, [...(map.get(r.subject) || []), r]);
  let at = 0;
  return [...map].sort((a, b) => rank(a[0]) - rank(b[0])).map(([subject, items]) => { const start = at; at += items.length; return { subject, items, start }; });
}

function Head({ subject, right }: { subject: string; right: string }) {
  return <View accessibilityRole="header" style={styles.sectionHead}>
    <T w="heavy" size={12} color={subjectColor(subject)} style={styles.caps}>{short(subject).toUpperCase()}</T>
    <View style={styles.rule} />
    <T w="bold" size={11} color={arena.muted}>{right}</T>
  </View>;
}

export function WeakSheet({ visible, onClose, chapters, topics }: { visible: boolean; onClose: () => void; chapters: Query<WeakChapters>; topics: Query<WeakTopics> }) {
  const router = useRouter(), insets = useSafeAreaInsets(), reduced = useReducedMotion(), sprint = useSprintStart(), n = useCardCount();
  const [part, setPart] = useState<Part>("chapters"), [subject, setSubject] = useState("");
  const [was, setWas] = useState(false);
  if (visible !== was) { setWas(visible); if (visible) { setPart("chapters"); setSubject(""); } }

  const rows = chapters.data?.items, list = topics.data?.topics;
  const cards = (rows || []).reduce((sum, r) => sum + r.remaining, 0);
  const subjects = useMemo(() => sections(rows || []).map((s) => ({ name: s.subject, cards: s.items.reduce((sum, r) => sum + r.remaining, 0) })), [rows]);
  const on = subjects.some((s) => s.name === subject) ? subject : ""; // a subject whose cards are all cleared falls back to All
  const shown = useMemo(() => sections((rows || []).filter((r) => !on || r.subject === on)), [rows, on]);
  const groups = useMemo(() => sections(list || []), [list]);

  // The sheet closes before the round opens, so it never sits on top of the cards.
  const replay = (c: WeakChapter) => { onClose(); router.push({ pathname: "/rapid/session", params: { exam: "JEE", subject: c.subject, chapter: c.chapter, revision: "1" } }); };
  const start = () => { onClose(); sprint(); };

  return <Modal visible={visible} transparent animationType={reduced ? "none" : "slide"} onRequestClose={onClose} statusBarTranslucent>
    <View style={styles.scrim}>
      <Pressable testID="rf-weak-sheet-backdrop" onPress={onClose} accessibilityLabel="Close weak cards" style={styles.flex} />
      <View testID="rf-weak-sheet" style={[styles.sheet, { paddingBottom: insets.bottom + 12 }]}>
        <View style={styles.handle} />
        <View style={styles.head}>
          <View style={styles.flex}>
            <GoldTitle size={20} testID="rf-weak-title">Weak cards</GoldTitle>
            <T testID="rf-weak-summary" w="bold" size={12} color={arena.aqua} numberOfLines={1}>
              {!rows ? "Finding your missed cards…" : cards ? `${plural(cards, "card")} to recover · ${plural(rows.length, "chapter")}` : "Nothing to recover right now"}
            </T>
          </View>
          <Pressable testID="rf-weak-sheet-close" onPress={onClose} accessibilityRole="button" accessibilityLabel="Close" style={styles.close}><Icon name="close" size={24} color={arena.muted} /></Pressable>
        </View>

        <View style={styles.pad}>
          <Segment prefix="rf-weak-part" value={part} onChange={setPart} items={[["chapters", rows?.length ? `Chapters · ${rows.length}` : "Chapters"], ["topics", list?.length ? `Topic Sprint · ${list.length}` : "Topic Sprint"]]} />
        </View>

        {part === "chapters" && subjects.length > 1 ? <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsWrap} contentContainerStyle={styles.tabs} testID="rf-weak-subjects">
          {[{ name: "", cards }, ...subjects].map((s) => {
            const picked = s.name === on, tint = s.name ? subjectColor(s.name) : arena.gold;
            return <Pressable key={s.name || "all"} testID={`rf-weak-subject-${s.name ? slug(s.name) : "all"}`} accessibilityRole="tab" accessibilityState={{ selected: picked }}
              accessibilityLabel={`${s.name ? short(s.name) : "All subjects"}, ${plural(s.cards, "card")}`} onPress={() => { tap(); setSubject(s.name); }} style={[styles.tab, picked && { backgroundColor: tint }]}>
              <T w="heavy" size={12} color={picked ? arena.badgeInk : arena.muted}>{s.name ? short(s.name) : "All"}</T>
              <View style={[styles.count, { backgroundColor: picked ? arena.badgeInk : tint }]}><T w="heavy" size={10} color={picked ? arena.text : arena.badgeInk}>{s.cards}</T></View>
            </Pressable>;
          })}
        </ScrollView> : null}

        {/* A new part or subject starts from the top of its own list. */}
        <ScrollView key={part + on} style={styles.flex} contentContainerStyle={styles.body} showsVerticalScrollIndicator={false}>
          {part === "chapters" ? <>
            <ErrorBox testID="rf-revision-error" error={chapters.error} retry={chapters.reload} />
            {chapters.loading && !rows ? <ActivityIndicator testID="rf-revision-loading" color={arena.aqua} /> : null}
            {shown.map((sec) => <React.Fragment key={sec.subject}>
              {on ? null : <Head subject={sec.subject} right={plural(sec.items.reduce((sum, r) => sum + r.remaining, 0), "card")} />}
              {sec.items.map((c, k) => {
                const i = sec.start + k;
                return <Pressable key={c.subject + c.chapter} testID={`rf-revise-chapter-${i}`} accessibilityRole="button" accessibilityLabel={`Replay ${c.chapter}, ${plural(c.remaining, "missed card")}`} onPress={() => { tap(); replay(c); }} style={styles.row}>
                  <View style={[styles.bar, { backgroundColor: subjectColor(c.subject) }]} />
                  <View style={styles.copy}>
                    <T testID={`rf-weak-chapter-${i}`} w="bold" size={15} color={arena.text} numberOfLines={2}>{c.chapter}</T>
                    <T testID={`rf-weak-count-${i}`} size={11.5} color={arena.muted} numberOfLines={1}>{plural(c.remaining, "card")} to recover · {plural(c.misses, "miss")}</T>
                  </View>
                  <View style={styles.replay}><Icon name="replay" size={16} color={arena.text} /><T w="heavy" size={12} color={arena.text}>REPLAY</T></View>
                </Pressable>;
              })}
            </React.Fragment>)}
            {rows && !rows.length ? <Note testID="rf-revision-empty">No missed cards waiting. Finish a sprint or a match: the cards you miss come here.</Note> : null}
            {rows?.length ? <T testID="rf-revision-rule" size={11} color={arena.faint} style={styles.center}>Wrong + timed-out cards only. Get one right to clear it.</T> : null}
          </> : <>
            <ErrorBox testID="rf-weak-sprint-error" error={topics.error} retry={topics.reload} />
            {topics.loading && !list ? <ActivityIndicator testID="rf-weak-sprint-loading" color={arena.aqua} /> : null}
            {groups.map((sec) => <React.Fragment key={sec.subject}>
              <Head subject={sec.subject} right={plural(sec.items.length, "subtopic")} />
              {sec.items.map((t, k) => <View key={t.chapter + t.topic} testID={`rf-weak-topic-${sec.start + k}`} style={styles.row}>
                <View style={[styles.bar, { backgroundColor: subjectColor(t.subject) }]} />
                <View style={styles.copy}>
                  <T w="bold" size={14.5} color={arena.text} numberOfLines={2}>{t.topic}</T>
                  <T size={11.5} color={arena.muted} numberOfLines={1}>{t.chapter}</T>
                </View>
                <View style={styles.miss}><T w="heavy" size={11} color={arena.badgeInk}>{plural(t.misses, "miss")}</T></View>
              </View>)}
            </React.Fragment>)}
            {list && !list.length ? <Note testID="rf-weak-sprint-empty">No weak subtopics yet. Play a few sprints or matches: the ones you miss show up here.</Note> : null}
          </>}
        </ScrollView>

        {part === "topics" && list?.length ? <View testID="rf-weak-sprint-panel" style={styles.footer}>
          <T w="bold" size={11.5} color={arena.muted} style={styles.center}>Only the subtopics you keep missing · {CARD_SECONDS} seconds a card</T>
          <RaisedButton testID="rf-weak-sprint-start" label="START SPRINT" sub={`${Math.min(n, topics.data!.cards)} cards · ${CARD_SECONDS} s each`} icon="bolt" height={60} streak onPress={start} />
        </View> : null}
      </View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, copy: { flex: 1, minWidth: 0, gap: 1 }, center: { textAlign: "center" }, caps: { letterSpacing: 1.5 }, pad: { paddingHorizontal: 18 },
  scrim: { flex: 1, backgroundColor: arena.scrim },
  sheet: { height: "86%", width: "100%", maxWidth: 560, alignSelf: "center", backgroundColor: arena.panel, borderTopLeftRadius: 28, borderTopRightRadius: 28, borderTopWidth: 1.5, borderColor: arena.rim, paddingTop: 8, gap: 10 },
  handle: { alignSelf: "center", width: 44, height: 5, borderRadius: 3, backgroundColor: arena.rim },
  head: { flexDirection: "row", alignItems: "center", gap: 8, paddingLeft: 18, paddingRight: 10 },
  close: { width: 44, height: 44, alignItems: "center", justifyContent: "center" },
  tabsWrap: { flexGrow: 0 }, tabs: { flexDirection: "row", gap: 6, paddingHorizontal: 18 },
  tab: { height: 44, paddingHorizontal: 14, borderRadius: 22, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, backgroundColor: arena.panelHi },
  count: { minWidth: 20, height: 20, borderRadius: 10, paddingHorizontal: 5, alignItems: "center", justifyContent: "center" },
  body: { paddingHorizontal: 18, paddingBottom: 12, gap: 8 },
  sectionHead: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 6 }, rule: { flex: 1, height: 1, backgroundColor: arena.rim },
  row: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 60, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  bar: { width: 5, height: 32, borderRadius: 3 },
  replay: { flexDirection: "row", alignItems: "center", gap: 4, height: 44, paddingHorizontal: 12, borderRadius: 14, backgroundColor: arena.teal, borderWidth: 1.5, borderColor: arena.tealOutline, borderBottomWidth: 4, borderBottomColor: arena.tealDeep },
  miss: { paddingHorizontal: 8, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center", backgroundColor: arena.gold },
  footer: { paddingHorizontal: 18, paddingTop: 10, gap: 8, borderTopWidth: 1, borderTopColor: arena.rim },
});
