import React, { useMemo, useState } from "react";
import { KeyboardAvoidingView, Modal, Platform, Pressable, ScrollView, TextInput, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { Icon, IconName, Press, T } from "@/src/components/ui";
import { colors, fonts, radius, space, subjectColor } from "@/src/theme";

const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const ICON: Record<string, IconName> = { Physics: "atom", Chemistry: "flask-outline", Mathematics: "function-variant", Biology: "dna" };
const short = (s: string) => (s === "Mathematics" ? "Maths" : s);

type Sub = { name: string; total: number; chapters: { name: string; count: number }[] };

// Full-height battleground picker: search, Mixed hero option, recent quick picks, chapters per subject.
export function ChapterSheet({ visible, onClose, subjects, subject, chapter, recent, onPick }: {
  visible: boolean; onClose: () => void; subjects: Sub[]; subject: string; chapter: string;
  recent: { subject: string; chapter: string }[]; onPick: (subject: string, chapter: string) => void;
}) {
  const insets = useSafeAreaInsets();
  const [q, setQ] = useState("");
  const [tab, setTab] = useState(subject);
  const [lastSubject, setLastSubject] = useState(subject);
  if (lastSubject !== subject) { setLastSubject(subject); setTab(subject); }
  const cur = subjects.find((s) => s.name === tab);
  const tint = subjectColor(tab);
  const query = q.trim().toLowerCase();
  const hits = useMemo(() => (query ? subjects.flatMap((s) => s.chapters.filter((c) => c.name.toLowerCase().includes(query)).map((c) => ({ ...c, subject: s.name }))) : []), [query, subjects]);
  const pick = (s: string, c: string) => { setQ(""); onPick(s, c); };

  const row = (s: string, c: { name: string; count: number }) => {
    const on = subject === s && chapter === c.name;
    return (
      <Press key={s + c.name} testID={"rf-chapter-" + slug(c.name)} disabled={!c.count} onPress={() => pick(s, c.name)}
        style={{ flexDirection: "row", alignItems: "center", gap: space.md, minHeight: 56, paddingHorizontal: space.md, borderRadius: radius.md, backgroundColor: on ? subjectColor(s) + "26" : colors.custom_gameCardHi, borderWidth: 1, borderColor: on ? subjectColor(s) : "transparent", opacity: c.count ? 1 : 0.4 }}>
        <View style={{ width: 6, height: 28, borderRadius: 3, backgroundColor: subjectColor(s) }} />
        <View style={{ flex: 1 }}>
          <T w="bold" size={15} color={colors.onSurfaceInverse}>{c.name}</T>
          {query ? <T size={11} color={colors.custom_gameMuted}>{short(s)}</T> : null}
        </View>
        <View style={{ paddingHorizontal: 8, height: 24, borderRadius: 12, justifyContent: "center", backgroundColor: colors.custom_gameBg }}>
          <T w="bold" size={11} color={colors.custom_gameMuted}>{c.count} cards</T>
        </View>
        {on ? <Icon name="check-circle" size={20} color={subjectColor(s)} /> : null}
      </Press>
    );
  };

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1 }}>
        <Pressable onPress={onClose} style={{ flex: 1, backgroundColor: colors.custom_gameBg + "B3" }} accessibilityLabel="Close chapter picker" />
        <View testID="rf-chapter-sheet" style={{ height: "86%", backgroundColor: colors.custom_gameCard, borderTopLeftRadius: 28, borderTopRightRadius: 28, paddingTop: space.sm, paddingBottom: insets.bottom + space.md, borderTopWidth: 1, borderColor: colors.custom_gameLine }}>
          <View style={{ alignSelf: "center", width: 44, height: 5, borderRadius: 3, backgroundColor: colors.custom_gameLine, marginBottom: space.md }} />
          <View style={{ paddingHorizontal: space.lg, gap: space.md }}>
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <T w="heavy" size={20} color={colors.onSurfaceInverse} style={{ flex: 1 }}>Choose your battleground</T>
              <Press testID="rf-chapter-close" onPress={onClose} style={{ width: 44, height: 44, alignItems: "center", justifyContent: "center" }}><Icon name="close" size={24} color={colors.custom_gameMuted} /></Press>
            </View>
            <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm, height: 52, paddingHorizontal: space.md, borderRadius: radius.lg, backgroundColor: colors.custom_gameBg, borderWidth: 1.5, borderColor: q ? colors.custom_neonCyan : colors.custom_gameLine }}>
              <Icon name="magnify" size={22} color={q ? colors.custom_neonCyan : colors.custom_gameMuted} />
              <TextInput testID="rf-chapter-search" value={q} onChangeText={setQ} placeholder="Search chapters…" placeholderTextColor={colors.custom_gameMuted} style={{ flex: 1, color: colors.onSurfaceInverse, fontFamily: fonts.bold, fontSize: 16 }} />
              {q ? <Press onPress={() => setQ("")} style={{ width: 32, height: 32, alignItems: "center", justifyContent: "center" }}><Icon name="close-circle" size={18} color={colors.custom_gameMuted} /></Press> : null}
            </View>
            {!query ? (
              <View style={{ flexDirection: "row", gap: 6 }}>
                {subjects.map((s) => (
                  <Press key={s.name} testID={"rf-sheet-subject-" + s.name.toLowerCase()} onPress={() => setTab(s.name)} style={{ flex: 1, height: 40, borderRadius: radius.pill, flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 4, backgroundColor: tab === s.name ? subjectColor(s.name) : colors.custom_gameCardHi }}>
                    <Icon name={ICON[s.name] || "book"} size={15} color={tab === s.name ? colors.onSurfaceInverse : colors.custom_gameMuted} />
                    <T w="heavy" size={12} color={tab === s.name ? colors.onSurfaceInverse : colors.custom_gameMuted}>{short(s.name)}</T>
                  </Press>
                ))}
              </View>
            ) : null}
          </View>
          <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: space.lg, gap: space.sm }}>
            {query ? (hits.length ? hits.map((c) => row(c.subject, c)) : <T size={14} color={colors.custom_gameMuted} style={{ textAlign: "center", marginTop: space.xl }}>No chapter matches “{q}”.</T>) : (
              <>
                <Press testID="rf-chapter-mixed" onPress={() => pick(tab, "")} scaleTo={0.97} style={{ borderRadius: radius.lg, overflow: "hidden", borderWidth: subject === tab && !chapter ? 2 : 0, borderColor: colors.onSurfaceInverse }}>
                  <LinearGradient colors={[tint, colors.custom_neonViolet]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md, minHeight: 72 }}>
                    <View style={{ width: 44, height: 44, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: colors.onSurfaceInverse + "33" }}><Icon name="shuffle-variant" size={24} color={colors.onSurfaceInverse} /></View>
                    <View style={{ flex: 1 }}>
                      <T w="heavy" size={16} color={colors.onSurfaceInverse}>Mixed {short(tab)}</T>
                      <T size={12} color={colors.onSurfaceInverse + "CC"}>Every chapter · {cur?.total ?? 0} cards</T>
                    </View>
                    {subject === tab && !chapter ? <Icon name="check-circle" size={22} color={colors.onSurfaceInverse} /> : <Icon name="chevron-right" size={22} color={colors.onSurfaceInverse} />}
                  </LinearGradient>
                </Press>
                {recent.length ? (
                  <View style={{ gap: space.sm, marginTop: space.sm }}>
                    <T w="heavy" size={11} color={colors.custom_gameMuted} style={{ letterSpacing: 1.5 }}>JUMP BACK IN</T>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm }}>
                      {recent.map((r) => (
                        <Press key={r.subject + r.chapter} testID={"rf-recent-" + slug(r.chapter)} onPress={() => pick(r.subject, r.chapter)} style={{ flexDirection: "row", alignItems: "center", gap: 6, height: 40, paddingHorizontal: 14, borderRadius: radius.pill, borderWidth: 1, borderColor: subjectColor(r.subject), backgroundColor: subjectColor(r.subject) + "1F" }}>
                          <Icon name="history" size={14} color={subjectColor(r.subject)} />
                          <T w="bold" size={13} color={colors.onSurfaceInverse}>{r.chapter}</T>
                        </Press>
                      ))}
                    </ScrollView>
                  </View>
                ) : null}
                <T w="heavy" size={11} color={colors.custom_gameMuted} style={{ letterSpacing: 1.5, marginTop: space.sm }}>{(cur?.chapters.length ?? 0) + " CHAPTERS"}</T>
                {(cur?.chapters || []).map((c) => row(tab, c))}
              </>
            )}
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}
