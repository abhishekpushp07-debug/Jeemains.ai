import React, { useState } from "react";
import { RefreshControl, ScrollView, View } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Button, Card, Chip, Empty, ErrorBox, Header, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { SeriesBanner, Series, Slot, SeriesExplainer } from "@/src/components/SeriesBanner";
import { colors, radius, space } from "@/src/theme";
import { istDate } from "@/src/navigation";

const stateLabel = (s: Slot) =>
  s.state === "live" ? (s.ready ? "LIVE TODAY" : "AWAITING PAPER") : s.state === "archive" ? "PRACTICE ARCHIVE" : s.state === "start_closed" ? "STARTS CLOSED" : s.state === "ended" ? "DAY ENDED" : "UPCOMING";

function SlotCard({ slot, attempt }: { slot: Slot; attempt?: any }) {
  const router = useRouter();
  const live = slot.state === "live" && slot.ready;
  return (
    <Card testID={"series-day-" + slot.day} style={{ gap: space.sm, borderColor: live ? colors.custom_series : colors.border }}>
      <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
        <T w="heavy" size={11} color={colors.custom_series}>TEST {String(slot.day).padStart(2, "0")}</T>
        <T w="heavy" size={11} color={live ? colors.success : colors.muted}>{stateLabel(slot)}</T>
      </View>
      <T w="heavy" size={16}>{slot.title}</T>
      <T size={12} color={colors.muted}>{istDate(slot.date)} · IST</T>
      <T size={12} color={colors.muted}>
        {!slot.ready ? "Paper not available yet. Only published papers can be started." : slot.state === "upcoming" ? "Opens 12:01 AM on its day." : slot.state === "start_closed" ? "New starts closed at 8:59 PM. Existing attempts keep their timer." : slot.state === "ended" ? "Results released. Archive opens at midnight." : "75 questions · 180 minutes · +4 / −1"}
      </T>
      {attempt ? <Button testID={"series-resume-" + slot.day} kind="secondary" label={attempt.resumable ? "Resume live attempt" : "Open live result"} color={colors.custom_series} onPress={() => router.push((attempt.resumable ? "/attempt/" : "/result/") + attempt.id as any)} /> : null}
      {slot.can_start && slot.set_id && (!attempt || slot.state === "archive") ? (
        <Button testID={"series-start-" + slot.day} label={slot.state === "archive" ? "Practise this paper" : "Check device & start"} color={colors.custom_series} onPress={() => router.push(`/set/${slot.set_id}`)} />
      ) : null}
    </Card>
  );
}

function Streak({ uid }: { uid: string }) {
  const s = useCached<any>(`u.${uid}.streak`, (signal) => api("/series/all-india-jee/streak", { signal }));
  if (s.error && !s.data) return <ErrorBox error="Your streak couldn’t load. Your submissions are safe." retry={s.reload} testID="streak-error" />;
  if (!s.data) return <Skeleton h={150} />;
  const d = s.data;
  const pct = Math.round((d.completed_count / (d.total_days || 62)) * 100);
  return (
    <Card testID="streak-card" style={{ gap: space.md }}>
      <View style={{ flexDirection: "row", alignItems: "center", gap: space.md }}>
        <View style={{ width: 52, height: 52, borderRadius: 26, backgroundColor: colors.custom_warningSoft, alignItems: "center", justifyContent: "center" }}>
          <Icon name="trophy" size={28} color={colors.custom_amber} />
        </View>
        <View style={{ flex: 1 }}>
          <T w="heavy" size={17}>Your 62-day run</T>
          <T size={12} color={colors.muted}>{d.stage === "prelaunch" ? "Starts 1 Dec 2026. No early points, no pretend progress." : d.today_state === "completed" ? "Today, you showed up." : "Only confirmed live completions count."}</T>
        </View>
      </View>
      <View style={{ flexDirection: "row", gap: space.sm }}>
        {[["Current", d.current_streak, "fire"], ["Best", d.best_streak, "trophy-outline"], ["Done", `${d.completed_count}/62`, "check-circle-outline"]].map(([l, v, ic]) => (
          <View key={String(l)} testID={"streak-" + String(l).toLowerCase()} style={{ flex: 1, padding: space.md, borderRadius: radius.md, backgroundColor: colors.surface, gap: 2 }}>
            <Icon name={ic as any} size={16} color={colors.custom_amber} />
            <T w="heavy" size={20}>{String(v)}</T>
            <T size={11} color={colors.muted}>{String(l)}</T>
          </View>
        ))}
      </View>
      <View accessibilityRole="progressbar" accessibilityValue={{ min: 0, max: 62, now: d.completed_count }} style={{ height: 10, borderRadius: 5, backgroundColor: colors.border, overflow: "hidden" }}>
        <View style={{ width: `${pct}%`, height: "100%", backgroundColor: colors.custom_series }} />
      </View>
      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 4 }}>
        {(d.milestones || []).map((m: any) => (
          <View key={m.days} testID={"streak-cup-" + m.days} style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, height: 28, borderRadius: radius.pill, backgroundColor: m.earned ? colors.custom_warningSoft : colors.surface, borderWidth: 1, borderColor: colors.border }}>
            <Icon name={m.earned ? "trophy" : "lock-outline"} size={13} color={m.earned ? colors.custom_amber : colors.muted} />
            <T w="bold" size={11}>{m.title} · {m.days}d</T>
          </View>
        ))}
      </View>
    </Card>
  );
}

export default function Live() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const series = useCached<Series>("series", (signal) => api("/series/all-india-jee", { signal }));
  const history = useCached<any>(user ? `u.${user.id}.serieshist` : null, (signal) => api("/series/all-india-jee/history?page=1", { signal }));
  const [tab, setTab] = useState<"today" | "archive" | "results">("today");
  const [open, setOpen] = useState(false);
  const d = series.data;
  const liveAttempt = history.data?.items?.find((a: any) => a.mode === "series_live" && a.series_date === d?.today);
  const archive = d?.slots.filter((s) => s.state === "archive").reverse() ?? [];

  return (
    <ScrollView testID="series-hub" style={{ flex: 1, backgroundColor: colors.surface }} contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: insets.bottom + space.xl, paddingHorizontal: space.lg, gap: space.lg }}
      refreshControl={<RefreshControl refreshing={false} onRefresh={() => { series.reload(); history.reload(); }} />}>
      <View style={{ marginHorizontal: -space.lg }}><Header title="Live JEE Series" eyebrow="All India · 62 days" color={colors.custom_series} onBack={() => (router.canGoBack() ? router.back() : router.replace("/(tabs)"))} /></View>
      <SeriesBanner series={d} error={series.error} compact />
      {user ? <Streak uid={user.id} /> : null}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: space.sm }} style={{ flexGrow: 0 }}>
        <Chip testID="series-tab-today" label="Live & schedule" icon="access-point" active={tab === "today"} color={colors.custom_series} onPress={() => setTab("today")} />
        <Chip testID="series-tab-archive" label="Archive" icon="archive-outline" active={tab === "archive"} color={colors.custom_series} onPress={() => setTab("archive")} />
        <Chip testID="series-tab-results" label="My results" icon="chart-bar" active={tab === "results"} color={colors.custom_series} onPress={() => setTab("results")} />
        <Chip testID="series-tab-about" label="How it works" icon="information-outline" onPress={() => setOpen(true)} />
      </ScrollView>
      <ErrorBox error={series.error && !d ? series.error : ""} retry={series.reload} />
      {!d && !series.error ? <Skeleton h={160} /> : null}
      {d && tab === "today" ? (
        <View style={{ gap: space.md }}>
          <T size={12} color={colors.muted} testID="series-timing-note">Live 12:01 AM–11:59 PM IST · Last start 8:59 PM · Results 11:59 PM</T>
          {d.today_slot ? <SlotCard slot={d.today_slot} attempt={liveAttempt} /> : (
            <Card testID="series-prelaunch"><Empty icon="calendar-star" title={d.today < d.first_date ? "The first challenge opens 1 December." : "The live series has ended."} body={d.today < d.first_date ? "Your 62-day schedule is below. Papers unlock only after publication and their opening time." : "Continue in the practice archive. Live results stay separate."} /></Card>
          )}
          <T w="heavy" size={17}>The 62-day schedule</T>
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }} testID="series-calendar">
            {d.slots.map((s) => {
              const today = s.date === d.today;
              return (
                <View key={s.day} testID={"series-calendar-day-" + s.day} accessibilityLabel={`Day ${s.day}, ${istDate(s.date)}, ${s.state}`} style={{ width: "18.4%", paddingVertical: 6, borderRadius: radius.sm, alignItems: "center", backgroundColor: today ? colors.custom_series : s.state === "archive" ? colors.custom_infoSoft : colors.surfaceSecondary, borderWidth: 1, borderColor: today ? colors.custom_series : colors.border }}>
                  <T w="heavy" size={13} color={today ? colors.onBrandSecondary : colors.onSurface}>{String(s.day).padStart(2, "0")}</T>
                  <T size={9} color={today ? colors.onBrandSecondary : colors.muted}>{istDate(s.date)}</T>
                </View>
              );
            })}
          </View>
        </View>
      ) : null}
      {d && tab === "archive" ? (archive.length ? <View style={{ gap: space.md }}>{archive.map((s) => <SlotCard key={s.day} slot={s} />)}</View> : <Card testID="series-archive-empty"><Empty icon="archive-outline" title="Your archive begins after day one." body="No past series days yet. The first paper enters the archive on 2 December 2026." /></Card>) : null}
      {tab === "results" ? (
        <View style={{ gap: space.md }}>
          <ErrorBox error={history.error && !history.data ? history.error : ""} retry={history.reload} />
          {history.data && !history.data.total ? <Card testID="series-history-empty"><Empty icon="book-open-variant" title="Your first attempt starts your story." body="Series attempts and released results appear here. No sample scores are shown." /></Card> : null}
          {history.data?.items?.map((a: any) => (
            <Press key={a.id} testID={"series-result-" + a.id} onPress={() => router.push(((a.resumable ? "/attempt/" : "/result/") + a.id) as any)}>
              <Card style={{ gap: 4 }}>
                <T w="bold" size={11} color={colors.custom_series}>{a.mode === "series_live" ? "LIVE ATTEMPT" : "ARCHIVE PRACTICE"} · {a.series_date ? istDate(a.series_date) : ""}</T>
                <T w="heavy" size={15}>{a.title}</T>
                <T size={13} color={colors.muted}>{a.summary ? `${a.summary.score} / ${a.summary.maximum} marks` : a.status === "embargoed" ? "Results release at 11:59 PM IST" : a.resumable ? "Attempt in progress" : "Preparing result"}</T>
              </Card>
            </Press>
          ))}
        </View>
      ) : null}
      <SeriesExplainer open={open} onClose={() => setOpen(false)} />
    </ScrollView>
  );
}
