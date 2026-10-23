import React, { useState } from "react";
import { Share, View } from "react-native";
import { useRouter } from "expo-router";
import { Icon, Press, Sheet, T, Button } from "@/src/components/ui";
import { colors, radius, space } from "@/src/theme";
import { istDate } from "@/src/navigation";

export type Slot = { day: number; date: string; state: string; ready: boolean; set_id: string | null; title: string; can_start: boolean; opens_at: number; last_start_at: number; closes_at: number };
export type Series = { id: string; title: string; first_date: string; last_date: string; total: number; today: string; server_now: number; slots: Slot[]; today_slot?: Slot | null };

export function availability(s?: Series | null) {
  if (!s) return { label: "Checking…", live: false };
  const t = s.today_slot;
  if (t?.ready && t.state === "live") return { label: "Live today", live: true };
  if (t?.ready && t.state === "start_closed") return { label: "Live · starts closed", live: true };
  if (s.today > s.last_date) return { label: "Practice archive", live: false };
  if (s.today < s.first_date) return { label: "Starts " + istDate(s.first_date), live: false };
  return { label: t && !t.ready ? "Awaiting paper" : "Scheduled", live: false };
}

export function SeriesBanner({ series, error, compact = false }: { series?: Series | null; error?: string; compact?: boolean }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const av = availability(series);
  return (
    <>
      <View testID="all-india-series-banner" style={{ backgroundColor: colors.custom_series, borderRadius: radius.lg, overflow: "hidden", padding: space.lg, paddingTop: space.md, gap: space.md }}>
        {/* True 45° top-right corner ribbon, clipped by the card */}
        <View pointerEvents="none" style={{ position: "absolute", top: 18, right: -38, width: 150, transform: [{ rotate: "45deg" }], backgroundColor: colors.custom_burgundy, paddingVertical: 5, alignItems: "center", shadowColor: colors.surfaceInverse, shadowOpacity: 0.3, shadowRadius: 4, elevation: 4 }}>
          <T testID="series-100ai-ribbon" w="heavy" size={12} color={colors.onBrandSecondary} style={{ letterSpacing: 1 }} accessibilityLabel="100% AI — series design branding">100% AI</T>
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <Icon name="creation" size={14} color={colors.custom_whiteA70} />
          <T size={12} color={colors.custom_whiteA70} testID="series-astra-credit">Created by <T w="heavy" size={12} color={colors.onBrandSecondary}>AI Astra</T></T>
        </View>
        <View style={{ paddingRight: 72 }}>
          <T w="semibold" size={15} color={colors.custom_whiteA70}>All India</T>
          <T w="heavy" size={compact ? 21 : 24} color={colors.onBrandSecondary} testID="series-banner-title">JEE Mains Test Series</T>
        </View>
        <View style={{ backgroundColor: colors.brandTertiary, borderRadius: radius.md, paddingVertical: space.sm, paddingHorizontal: space.md, gap: 2 }}>
          <T w="heavy" size={17} color={colors.custom_burgundy} testID="series-score-200-tagline">Score 200+ with AI</T>
          <T w="bold" size={12} color={colors.onSurface}>AI analysed PYQ based test series</T>
        </View>
        <View style={{ flexDirection: "row", flexWrap: "wrap", gap: space.sm, alignItems: "center" }}>
          <T size={12} w="medium" color={colors.custom_whiteA70}>{series ? `${istDate(series.first_date)} – ${istDate(series.last_date)}` : "1 Dec – 31 Jan"} · {series?.total ?? 62} tests · 3 hrs</T>
          <View testID="series-availability-badge" style={{ flexDirection: "row", alignItems: "center", gap: 4, paddingHorizontal: 8, paddingVertical: 3, borderRadius: radius.pill, backgroundColor: av.live ? colors.success : colors.custom_whiteA15 }}>
            <Icon name={av.live ? "access-point" : "calendar-clock"} size={12} color={colors.onBrandSecondary} />
            <T w="bold" size={11} color={colors.onBrandSecondary}>{av.label}</T>
          </View>
        </View>
        {error ? <T size={11} color={colors.custom_whiteA70}>Live status unavailable. Open the hub to retry.</T> : null}
        <View style={{ flexDirection: "row", gap: space.sm }}>
          <Press testID="series-open-hub-button" onPress={() => router.push("/live")} style={{ flex: 1, minHeight: 46, borderRadius: radius.md, backgroundColor: colors.surfaceSecondary, alignItems: "center", justifyContent: "center", flexDirection: "row", gap: 6 }}>
            <T w="heavy" size={14} color={colors.custom_series}>Open series hub</T>
            <Icon name="arrow-top-right" size={16} color={colors.custom_series} />
          </Press>
          <Press testID="series-explainer-button" onPress={() => setOpen(true)} accessibilityLabel="How the series works" style={{ width: 46, minHeight: 46, borderRadius: radius.md, borderWidth: 1, borderColor: colors.custom_whiteA70, alignItems: "center", justifyContent: "center" }}>
            <Icon name="information-outline" size={20} color={colors.onBrandSecondary} />
          </Press>
        </View>
      </View>
      <SeriesExplainer open={open} onClose={() => setOpen(false)} />
    </>
  );
}

export function SeriesExplainer({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <Sheet visible={open} onClose={onClose} testID="series-explainer">
      <T w="bold" size={11} color={colors.custom_series} style={{ letterSpacing: 1 }}>THE DAILY FULL-SYLLABUS CHALLENGE</T>
      <T w="heavy" size={22}>62 days. One focused mission.</T>
      <T w="bold" size={14}>AI analysed PYQ based test series</T>
      {[
        "One full mock each day · 75 questions · 300 marks · 180 minutes.",
        "Live window 12:01 AM–11:59 PM IST. Last start 8:59 PM IST.",
        "One live attempt per profile. Resume keeps the original deadline.",
        "Live results and solutions unlock at 11:59 PM IST for fairness.",
        "Previous days open in the practice archive at midnight.",
      ].map((x) => (
        <View key={x} style={{ flexDirection: "row", gap: 8 }}>
          <Icon name="check-circle" size={16} color={colors.custom_series} />
          <T size={13} style={{ flex: 1 }}>{x}</T>
        </View>
      ))}
      <T size={11} color={colors.muted} testID="series-claims-disclaimer">
        Independent practice, not affiliated with NTA. The 80-factor PYQ analysis is the series’ stated design approach, not an AI prediction of the official paper. “AI Astra” and “100% AI” describe the creator’s AI-led design, not an audit of every explanation. “World best” is an ambition, not a verified ranking. “Score 200+ with AI” is a practice goal, not a guarantee.
      </T>
      <Button testID="series-explainer-close" label="Got it" onPress={onClose} color={colors.custom_series} />
    </Sheet>
  );
}

export function useShare() {
  return () =>
    Share.share({ message: "JEELIVE.AI — free JEE Main, BITSAT & COMEDK practice: chapter tests, 62-day All India series and 20-second Rapid Fire formula cards. Free for everyone. https://jeelive.ai" }).catch(() => {});
}
