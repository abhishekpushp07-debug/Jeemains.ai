import React, { useState } from "react";
import { ScrollView, TextInput, View } from "react-native";
import { useRouter } from "expo-router";
import { LinearGradient } from "expo-linear-gradient";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { rf } from "@/src/api/client";
import { useCached } from "@/src/useCached";
import { Button, Card, Chip, Empty, ErrorBox, Icon, Press, Skeleton, T } from "@/src/components/ui";
import { colors, fonts, radius, space, subjectColor } from "@/src/theme";
import { usesNativeTabs } from "@/src/navigation";

const pick = { subject: "Physics", chapter: "" as string };

export default function RapidHome() {
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const [subject, setSubject] = useState(pick.subject);
  const [chapter, setChapter] = useState(pick.chapter);
  Object.assign(pick, { subject, chapter });
  const cat = useCached<any>("rf.catalog", () => rf("/catalog", user?.id || "guest-viewer"));
  const hist = useCached<any>(user ? `u.${user.id}.rfhist` : null, () => rf("/history", user!.id), false);
  const duels = useCached<any>(user ? `u.${user.id}.duels` : null, () => rf("/duels", user!.id), false);
  const [code, setCode] = useState("");
  const sub = cat.data?.subjects?.find((s: any) => s.name === subject);
  const chosen = chapter ? sub?.chapters.find((c: any) => c.name === chapter) : null;
  const available = chosen ? chosen.count : sub?.total ?? 0;
  const tint = subjectColor(subject);

  return (
    <ScrollView testID="rapid-fire-home" style={{ flex: 1, backgroundColor: colors.surface }} contentContainerStyle={{ paddingTop: insets.top + space.sm, paddingBottom: (usesNativeTabs ? insets.bottom : 0) + space.xl, paddingHorizontal: space.lg, gap: space.lg }}>
      <LinearGradient colors={[colors.custom_darkCard, colors.surfaceInverse]} style={{ borderRadius: radius.lg, padding: space.xl, gap: space.sm, overflow: "hidden" }}>
        <View style={{ position: "absolute", right: -10, top: -10, opacity: 0.12 }}><Icon name="lightning-bolt" size={150} color={colors.custom_examBitsat} /></View>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <Icon name="lightning-bolt" size={18} color={colors.custom_examBitsat} />
          <T w="heavy" size={12} color={colors.custom_examBitsat} style={{ letterSpacing: 1.2 }}>RAPID FIRE</T>
        </View>
        <T w="heavy" size={26} color={colors.onSurfaceInverse}>10-minute formula sprint</T>
        <T size={13} color={colors.custom_whiteA70}>30 cards · max 20 seconds each · tap to answer · no negative marking. Pure recall — no pen needed.</T>
      </LinearGradient>

      <View style={{ gap: space.sm }}>
        <T w="heavy" size={16}>1 · Subject</T>
        <View style={{ flexDirection: "row", gap: space.sm }}>
          {["Physics", "Chemistry", "Mathematics"].map((s) => (
            <Press key={s} testID={"rf-subject-" + s.toLowerCase()} onPress={() => { setSubject(s); setChapter(""); }} style={{ flex: 1, height: 64, borderRadius: radius.md, alignItems: "center", justifyContent: "center", gap: 2, backgroundColor: subject === s ? subjectColor(s) : colors.surfaceSecondary, borderWidth: 1, borderColor: subject === s ? subjectColor(s) : colors.border }}>
              <Icon name={s === "Physics" ? "atom" : s === "Chemistry" ? "flask-outline" : "function-variant"} size={20} color={subject === s ? colors.onBrandPrimary : subjectColor(s)} />
              <T w="heavy" size={12} color={subject === s ? colors.onBrandPrimary : colors.onSurface}>{s === "Mathematics" ? "Maths" : s}</T>
            </Press>
          ))}
        </View>
      </View>

      <View style={{ gap: space.sm }}>
        <T w="heavy" size={16}>2 · Chapter or mixed</T>
        <ErrorBox error={cat.error && !cat.data ? cat.error : ""} retry={cat.reload} testID="rf-catalog-error" />
        {!cat.data && !cat.error ? <Skeleton h={120} /> : null}
        {sub ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ height: 56, flexGrow: 0, marginHorizontal: -space.lg }} contentContainerStyle={{ gap: space.sm, paddingHorizontal: space.lg, alignItems: "center" }}>
            <Chip testID="rf-chapter-mixed" label={`Mixed ${subject}`} icon="shuffle-variant" active={!chapter} color={tint} count={sub.total} onPress={() => setChapter("")} />
            {sub.chapters.map((c: any) => (
              <Chip key={c.name} testID={"rf-chapter-" + c.name.toLowerCase().replace(/[^a-z0-9]+/g, "-")} label={c.name} active={chapter === c.name} color={tint} count={c.count} onPress={() => c.count && setChapter(c.name)} />
            ))}
          </ScrollView>
        ) : null}
      </View>

      <Card testID="rf-session-summary" style={{ gap: space.sm }}>
        <T w="heavy" size={15}>{chapter || `Mixed ${subject}`}</T>
        <T size={13} color={colors.muted}>{available ? `${Math.min(30, available)} cards this session${available < 30 ? " (only " + available + " available — no repeats added)" : ""} · 20 s max per card · max ~10 min active time` : "No reviewed cards available for this selection yet."}</T>
        <Button testID="rf-start-button" label="Start Rapid Fire" icon="lightning-bolt" color={colors.custom_amber} disabled={!available || !user} onPress={() => router.push({ pathname: "/rapid/session", params: { subject, chapter } })} />
        <T size={10} color={colors.muted}>{cat.data?.note} Rapid Fire never changes mock marks, ranks or the series streak.</T>
      </Card>

      <Card testID="rf-duel-card" style={{ gap: space.md, borderColor: colors.custom_amber }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: space.sm }}>
          <View style={{ width: 44, height: 44, borderRadius: 14, backgroundColor: colors.custom_warningSoft, alignItems: "center", justifyContent: "center" }}>
            <Icon name="sword-cross" size={24} color={colors.custom_amber} />
          </View>
          <View style={{ flex: 1 }}>
            <T w="heavy" size={16}>Duel another student</T>
            <T size={12} color={colors.muted}>Same 30 cards, live score race · {chapter || `Mixed ${subject}`}</T>
          </View>
        </View>
        <View style={{ flexDirection: "row", gap: space.sm }}>
          <Button testID="rf-duel-random" label="Random match" icon="account-search" color={colors.custom_amber} disabled={!available || !user} onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "random", subject, chapter } })} style={{ flex: 1 }} />
          <Button testID="rf-duel-invite" label="WhatsApp friend" icon="whatsapp" color={colors.success} disabled={!available || !user} onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "invite", subject, chapter } })} style={{ flex: 1 }} />
        </View>
        <View style={{ flexDirection: "row", gap: space.sm, alignItems: "center" }}>
          <TextInput testID="rf-duel-code-input" value={code} onChangeText={(t) => setCode(t.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6))} placeholder="Friend’s code" placeholderTextColor={colors.muted} autoCapitalize="characters"
            style={{ flex: 1, height: 50, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: space.md, fontFamily: fonts.bold, fontSize: 16, letterSpacing: 3, color: colors.onSurface, backgroundColor: colors.surface }} />
          <Button testID="rf-duel-join" kind="secondary" label="Join" disabled={code.length < 6 || !user} onPress={() => router.push({ pathname: "/rapid/duel", params: { mode: "join", code } })} />
        </View>
        {duels.data?.items?.length ? (
          <T size={12} color={colors.muted} testID="rf-duel-record">Duel record: {duels.data.items.filter((x: any) => x.won).length} won · {duels.data.items.filter((x: any) => x.tie).length} tied · {duels.data.items.filter((x: any) => !x.won && !x.tie).length} lost (last {duels.data.items.length})</T>
        ) : null}
      </Card>

      <View style={{ gap: space.sm }}>
        <T w="heavy" size={16}>Your Rapid Fire history</T>
        {hist.data?.totals?.sessions ? (
          <T size={13} color={colors.muted} testID="rf-history-totals">{hist.data.totals.sessions} sessions · {hist.data.totals.correct}/{hist.data.totals.cards} cards correct</T>
        ) : null}
        {hist.data?.items?.length ? hist.data.items.slice(0, 6).map((s: any) => (
          <Press key={s.id} testID={"rf-history-" + s.id} onPress={() => router.push({ pathname: "/rapid/session", params: { review: s.id } })}>
            <Card style={{ flexDirection: "row", alignItems: "center", gap: space.md, padding: space.md }}>
              <View style={{ width: 44, height: 44, borderRadius: 12, backgroundColor: subjectColor(s.subject), alignItems: "center", justifyContent: "center" }}>
                <T w="heavy" size={15} color={colors.onBrandPrimary}>{s.summary?.score}/{s.summary?.total}</T>
              </View>
              <View style={{ flex: 1 }}>
                <T w="bold" size={14}>{s.chapter || "Mixed " + s.subject}{s.mode === "repeat_missed" ? " · missed repeat" : ""}</T>
                <T size={12} color={colors.muted}>{s.summary?.incorrect} wrong · {s.summary?.skipped} skipped · {s.summary?.timed_out} timed out</T>
              </View>
              <Icon name="chevron-right" size={22} color={colors.muted} />
            </Card>
          </Press>
        )) : hist.data ? <Card testID="rf-history-empty"><Empty icon="lightning-bolt-outline" title="No sessions yet" body="Your first 3-minute burst will show here." /></Card> : null}
      </View>
    </ScrollView>
  );
}
