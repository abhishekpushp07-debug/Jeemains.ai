import React, { useEffect, useState } from "react";
import { FlatList, TextInput, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Button, Card, Chip, Empty, ErrorBox, Header, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { colors, fonts, radius, space, subjectColor } from "@/src/theme";
import { examBySlug, fmtClock, unixDate } from "@/src/navigation";

const ORDER = ["Physics", "Chemistry", "Mathematics"];
// Remember subject/search per exam+kind so Back never resets the list.
const remembered: Record<string, { subject: string; q: string }> = {};

export function attemptAction(s: any): { label: string; to: string; tone: string } {
  const a = s.attempt;
  if (a?.status === "active" || a?.resumable) return { label: "Resume", to: `/attempt/${a.id}`, tone: colors.success };
  if (a?.id && (a.status === "completed" || a.result_available)) return { label: "Result", to: `/result/${a.id}`, tone: colors.brandPrimary };
  return { label: "Start", to: `/set/${s.id}`, tone: colors.surfaceInverse };
}

function SetRow({ s }: { s: any }) {
  const router = useRouter();
  const act = attemptAction(s);
  const available = s.live_enabled !== false && s.status === "published";
  const subj = s.chapter_subject || s.subjects?.[0];
  return (
    <Press testID={"set-row-" + s.id} disabled={!available} onPress={() => router.push(act.to as any)}>
      <Card style={{ flexDirection: "row", gap: space.md, alignItems: "center", padding: space.md }}>
        <View style={{ width: 46, height: 46, borderRadius: 14, backgroundColor: subjectColor(subj), alignItems: "center", justifyContent: "center" }}>
          <T w="heavy" size={16} color={colors.onBrandPrimary}>{s.chapter_number ?? s.mock_number ?? "•"}</T>
        </View>
        <View style={{ flex: 1, gap: 2 }}>
          <T w="heavy" size={15} numberOfLines={2}>{s.title}</T>
          <T size={12} color={colors.muted}>{s.count} Q · {s.rules?.minutes ? s.rules.minutes + " min" : "Untimed"} · +{s.rules?.correct}/{s.rules?.wrong} · {s.maximum} marks</T>
          {s.saved ? <T size={11} w="bold" color={colors.custom_amber}>Saved</T> : null}
        </View>
        {available ? (
          <View style={{ paddingHorizontal: 12, height: 34, borderRadius: radius.pill, backgroundColor: act.tone, alignItems: "center", justifyContent: "center" }}>
            <T w="heavy" size={12} color={colors.onBrandPrimary}>{act.label}</T>
          </View>
        ) : <T size={11} w="bold" color={colors.muted}>Unavailable</T>}
      </Card>
    </Press>
  );
}

function HistoryRow({ a }: { a: any }) {
  const router = useRouter();
  return (
    <Press testID={"history-row-" + a.id} onPress={() => router.push(((a.resumable ? "/attempt/" : "/result/") + a.id) as any)}>
      <Card style={{ gap: 4 }}>
        <T w="bold" size={11} color={colors.muted}>{unixDate(a.started_at)} · {a.status}</T>
        <T w="heavy" size={15}>{a.title}</T>
        <T size={13} color={colors.brandPrimary} w="bold">{a.summary ? `${a.summary.score} / ${a.summary.maximum}` : a.resumable ? `Resume${a.remaining_seconds ? " · " + fmtClock(Math.round(a.remaining_seconds)) + " left" : ""}` : a.status === "embargoed" ? "Result sealed until release" : "Preparing result"}</T>
      </Card>
    </Press>
  );
}

export default function Catalogue() {
  const { slug, kind } = useLocalSearchParams<{ slug: string; kind: "mocks" | "chapters" | "history" }>();
  const exam = examBySlug(slug);
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const memKey = `${slug}.${kind}`;
  const [subject, setSubject] = useState(remembered[memKey]?.subject ?? (kind === "chapters" ? "Physics" : ""));
  const [q, setQ] = useState(remembered[memKey]?.q ?? "");
  const [query, setQuery] = useState(q);
  const [page, setPage] = useState(1);
  remembered[memKey] = { subject, q: query };
  useEffect(() => {
    const t = setTimeout(() => { if (q.trim() !== query) { setPage(1); setQuery(q.trim()); } }, 300);
    return () => clearTimeout(t);
  }, [q, query]);

  const path = kind === "history"
    ? `/exam-navigation/${slug}/history?page=${page}`
    : `/exam-navigation/${slug}/catalogue?${new URLSearchParams({ kind: kind!, subject: kind === "chapters" ? subject : "", q: query, page: String(page) })}`;
  const valid = !!slug && (kind === "history" || kind === "mocks" || kind === "chapters");
  const res = useCached<any>(user && valid ? `u.${user.id}.${path}` : null, (signal) => api(path, { signal }));
  const fullKey = user && valid ? `u.${user.id}.${path}` : null;
  const items: any[] = res.data && res.dataKey === fullKey ? res.data.items : [];
  const subjects = Object.keys(res.data?.subject_counts || {}).sort((a, b) => (ORDER.indexOf(a) + 99) % 99 - (ORDER.indexOf(b) + 99) % 99);
  const subjectList = subjects.length ? subjects : ORDER;
  const title = kind === "history" ? "Results & history" : kind === "chapters" ? "Chapter-wise" : "Mock tests";

  return (
    <View testID={`catalogue-${slug}-${kind}`} style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <Header title={title} eyebrow={exam?.name} onBack={() => router.back()} />
      {kind !== "history" ? (
        <View style={{ paddingHorizontal: space.lg }}>
          <View style={{ flexDirection: "row", alignItems: "center", backgroundColor: colors.surfaceSecondary, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: space.md, height: 46 }}>
            <Icon name="magnify" size={20} color={colors.muted} />
            <TextInput testID="catalogue-search-input" value={q} onChangeText={setQ} placeholder={kind === "chapters" ? "Find a chapter…" : "Find a mock test…"} placeholderTextColor={colors.muted} maxLength={100} style={{ flex: 1, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, paddingHorizontal: space.sm }} />
            {q ? <Press testID="catalogue-clear-search" onPress={() => setQ("")} accessibilityLabel="Clear search"><Icon name="close-circle" size={18} color={colors.muted} /></Press> : null}
          </View>
        </View>
      ) : null}
      {kind === "chapters" ? (
        <View style={{ height: 56, justifyContent: "center" }}>
          <FlatList horizontal showsHorizontalScrollIndicator={false} data={subjectList} keyExtractor={(x) => x}
            contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}
            renderItem={({ item }) => <Chip testID={"catalogue-subject-" + item.toLowerCase()} label={item} color={subjectColor(item)} active={subject === item} count={res.data?.subject_counts?.[item]} onPress={() => { setPage(1); setSubject(item); }} />} />
        </View>
      ) : <View style={{ height: space.md }} />}
      <FlatList
        data={items}
        keyExtractor={(x) => x.id}
        renderItem={({ item }) => (kind === "history" ? <HistoryRow a={item} /> : <SetRow s={item} />)}
        contentContainerStyle={{ paddingHorizontal: space.lg, paddingBottom: insets.bottom + space.xl, gap: space.md }}
        ListHeaderComponent={<>
          <ErrorBox error={res.error} retry={res.reload} testID="catalogue-error" />
          {res.data ? <T size={12} color={colors.muted} testID="catalogue-count">{res.data.total} {kind === "history" ? "attempts" : "live " + (kind === "chapters" ? "chapter tests" : "mock tests")}</T> : null}
        </>}
        ListEmptyComponent={(!res.data || res.dataKey !== fullKey) && !res.error ? <View style={{ gap: space.md }}><Skeleton h={76} /><Skeleton h={76} /><Skeleton h={76} /></View> : res.data ? (
          <Card testID="catalogue-empty"><Empty icon={kind === "history" ? "history" : "file-document-outline"} title={query ? "No matching tests." : kind === "history" ? "No attempts yet." : kind === "mocks" ? "Full-length mocks are not live yet." : "No live tests for this subject."}
            body={query ? "Try another search." : kind === "history" ? "Your attempts for this exam will appear here." : `Reviewed ${exam?.name} papers appear here when published. Nothing fake is shown.`}
            action={kind === "mocks" ? <Button testID="catalogue-try-chapters" kind="secondary" label="Try chapter-wise practice" onPress={() => router.replace(`/catalogue?slug=${slug}&kind=chapters`)} /> : undefined} /></Card>
        ) : undefined}
        ListFooterComponent={res.data?.pages > 1 ? (
          <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
            <Button testID="catalogue-prev-page" kind="secondary" label="Previous" disabled={page <= 1} onPress={() => setPage((p) => p - 1)} style={{ flex: 1 }} />
            <T w="bold" size={13} testID="catalogue-page">{page} / {res.data.pages}</T>
            <Button testID="catalogue-next-page" kind="secondary" label="Next" disabled={page >= res.data.pages} onPress={() => setPage((p) => p + 1)} style={{ flex: 1 }} />
          </View>) : undefined}
      />
    </View>
  );
}
