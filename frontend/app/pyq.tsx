import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppState, FlatList, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { getPyqCatalogue, openPyq, paperState, PyqCatalogue, PyqPaper, resumePyq, sortPapers } from "@/src/api/pyq";
import { useCached } from "@/src/useCached";
import { PyqPaperCard } from "@/src/components/PyqPaperCard";
import { Button, Chip, Empty, ErrorBox, Header, Icon, Skeleton, T } from "@/src/components/ui";
import { colors, space } from "@/src/theme";
import { ReadyToStart } from "@/src/components/player/ReadyToStart";

export default function PyqPapers() {
  const { user } = useAuth();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const papers = useCached<PyqCatalogue>(user ? `u.${user.id}.pyq.jee-main` : null, getPyqCatalogue, false);
  const [year, setYear] = useState<number | null>(null);
  const [shift, setShift] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [failedPaper, setFailedPaper] = useState("");
  const [readyPaper, setReadyPaper] = useState<PyqPaper | null>(null);
  const first = useRef(true);
  const alive = useRef(true);
  const locked = useRef(false);
  const uid = useRef(user?.id);
  useEffect(() => { uid.current = user?.id; }, [user?.id]);
  const refresh = papers.reload;
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  useFocusEffect(useCallback(() => { if (first.current) first.current = false; else refresh(); }, [refresh]));
  useEffect(() => { const sub = AppState.addEventListener("change", (state) => { if (state === "active") refresh(); }); return () => sub.remove(); }, [refresh]);

  const items = useMemo(() => sortPapers(papers.data?.items || []), [papers.data]);
  const years = useMemo(() => [...new Set(items.map((p) => p.year))].sort((a, b) => b - a), [items]);
  const shifts = useMemo(() => [...new Set(items.filter((p) => !year || p.year === year).map((p) => String(p.shift)))].sort(), [items, year]);
  const selectedYear = year && years.includes(year) ? year : null;
  const selectedShift = shifts.includes(shift) ? shift : "";
  const visible = items.filter((p) => (!selectedYear || p.year === selectedYear) && (!selectedShift || String(p.shift) === selectedShift));

  async function open(paper: PyqPaper, checkedAt = 0) {
    if (!user || locked.current) return;
    const owner = user.id;
    locked.current = true;
    setBusy(paper.id);
    setError("");
    setFailedPaper("");
    try {
      const attempt = paperState(paper) === "active" ? await resumePyq(paper) : await openPyq(owner, paper, checkedAt);
      if (!alive.current || uid.current !== owner) return;
      setReadyPaper(null);
      router.push(((attempt.status === "active" ? "/attempt/" : "/result/") + encodeURIComponent(attempt.id)) as any);
    } catch (e: any) {
      if (alive.current && uid.current === owner) { setFailedPaper(paper.id); setError(e.message || "Could not open this paper. Please retry."); }
    } finally {
      locked.current = false;
      if (alive.current) setBusy(null);
    }
  }

  return <View testID="pyq-screen" style={[styles.screen, { paddingTop: insets.top + space.sm }]}>
    <Header title="PYQ papers" eyebrow="JEE MAIN" testID="pyq-header" backTestID="pyq-back-button" onBack={() => router.canGoBack() ? router.back() : router.replace("/(tabs)/jee")} />
    <FlatList testID="pyq-paper-list" data={visible} keyExtractor={(p) => p.id} showsVerticalScrollIndicator={false}
      refreshing={papers.loading && !!papers.data} onRefresh={refresh}
      contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + space.xl }]}
      ListHeaderComponent={<View style={styles.intro}>
        <View style={styles.heading}>
          <View style={styles.copy}><T testID="pyq-title" size={28} w="heavy">Real papers.</T><T testID="pyq-subtitle" size={28} w="heavy" color={colors.brandText}>Your next attempt.</T></View>
          <View style={styles.emblem}><Icon name="file-document-check-outline" size={30} color={colors.brandText} /></View>
        </View>
        <T testID="pyq-description" size={13} color={colors.muted}>Pick a paper and start. Your place is saved when you leave.</T>
        {papers.data ? <T testID="pyq-total" size={12} w="bold" color={colors.brandText}>{papers.data.total} {papers.data.total === 1 ? "paper" : "papers"} available{selectedYear || selectedShift ? ` · ${visible.length} shown` : ""}</T> : null}
        {years.length ? <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters} testID="pyq-year-filters">
          <Chip testID="pyq-year-all" label="All years" active={!selectedYear} onPress={() => { setYear(null); setShift(""); }} />
          {years.map((y) => <Chip testID={`pyq-year-${y}`} key={y} label={String(y)} active={selectedYear === y} onPress={() => { setYear(y); setShift(""); }} />)}
        </ScrollView> : null}
        {shifts.length > 1 ? <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters} testID="pyq-shift-filters">
          <Chip testID="pyq-shift-all" label="All shifts" active={!selectedShift} onPress={() => setShift("")} />
          {shifts.map((s) => <Chip testID={`pyq-shift-${s}`} key={s} label={`Shift ${s}`} active={selectedShift === s} onPress={() => setShift(s)} />)}
        </ScrollView> : null}
        <ErrorBox testID="pyq-load-error" error={papers.error} retry={refresh} />
      </View>}
      renderItem={({ item, index }) => <View style={styles.item}>
        {index === 0 || visible[index - 1].year !== item.year ? <T testID={`pyq-section-${item.year}`} size={11} color={colors.muted} w="heavy" style={styles.section}>{item.year} PAPERS</T> : null}
        <PyqPaperCard paper={item} busy={busy === item.id} locked={!!busy} error={failedPaper === item.id ? error : ""} onOpen={() => { if (paperState(item) === "active") void open(item); else { setError(""); setReadyPaper(item); } }} onResult={(id) => router.push(`/result/${encodeURIComponent(id)}`)} />
      </View>}
      ListEmptyComponent={!papers.data && !papers.error ? <View testID="pyq-loading" style={styles.loading}><Skeleton h={200} /><Skeleton h={200} /></View> : !papers.error ?
        <View testID="pyq-empty" style={styles.empty}><Empty icon="file-document-outline" title={items.length ? "No papers match these filters" : "No PYQs returned for this account"}
          body={items.length ? "Try all years and shifts to see the available papers." : "The connected website hasn't returned any papers for this account. Refresh to check again. Your existing tests are safe."}
          action={<Button testID="pyq-empty-refresh" label={items.length ? "Reset filters" : "Refresh papers"} kind="secondary" icon="refresh" onPress={() => { setYear(null); setShift(""); refresh(); }} />} /></View> : undefined}
      ListFooterComponent={papers.data ? <View style={styles.footer}>
        {papers.data.source_note ? <T testID="pyq-source-note" size={11} color={colors.mutedSecondary}>{papers.data.source_note}</T> : null}
        {items.length ? <T testID="pyq-start-rules" size={11} color={colors.mutedSecondary}>Each paper follows its own timing and marking rules. Check readiness, then start without a countdown. Re-attempt never replaces previous results.</T> : null}
      </View> : undefined} />
    {readyPaper ? <ReadyToStart key={readyPaper.id} setId={readyPaper.id} title={readyPaper.title || "JEE Main PYQ"} busy={!!busy} error={error} onClose={() => setReadyPaper(null)} onStart={time => void open(readyPaper, time)} /> : null}
  </View>;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.surface },
  list: { paddingHorizontal: space.lg, gap: space.lg },
  intro: { gap: space.md, paddingTop: space.sm },
  heading: { flexDirection: "row", alignItems: "center", gap: space.md },
  copy: { flex: 1 },
  emblem: { width: 60, height: 60, borderRadius: 20, backgroundColor: colors.brandTertiary, borderWidth: 1, borderColor: colors.brandLine, alignItems: "center", justifyContent: "center" },
  filters: { gap: space.sm, paddingRight: space.lg },
  item: { gap: space.sm }, section: { letterSpacing: 1.4, marginTop: space.xs },
  loading: { gap: space.lg }, empty: { backgroundColor: colors.surfaceSecondary, borderRadius: 20, borderWidth: 1, borderColor: colors.border },
  footer: { gap: space.sm, paddingVertical: space.sm },
});