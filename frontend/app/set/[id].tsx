import React, { useEffect, useRef, useState } from "react";
import { ScrollView, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useAuth } from "@/src/auth";
import { api, del, post, uuid } from "@/src/api/client";
import { storage } from "@/src/utils/storage";
import { invalidate } from "@/src/useCached";
import { Button, Card, ErrorBox, Header, Icon, Notice, Press, Skeleton, Stat, T } from "@/src/components/ui";
import { colors, radius, space, subjectColor } from "@/src/theme";

export default function SetDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  const { user } = useAuth();
  const [s, setS] = useState<any>(null);
  const [error, setError] = useState("");
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(false);
  const [reload, setReload] = useState(0);
  const key = useRef<string | null>(null);
  const startKeyName = `start.${user?.id}.${id}`;

  useEffect(() => {
    let alive = true;
    setError("");
    api(`${user ? "/my/sets/" : "/sets/"}${id}`).then((d) => { if (alive) { setS(d); setSaved(!!d.saved); } }).catch((e) => alive && setError(e.message));
    storage.getItem<string | null>(startKeyName, null).then(async (k) => {
      key.current = k || uuid();
      if (!k) await storage.setItem(startKeyName, key.current);
    });
    return () => { alive = false; };
  }, [id, user, reload, startKeyName]);

  // One tap: the device/connection check the server needs runs silently, then the attempt opens.
  async function start() {
    setBusy(true);
    setError("");
    try {
      if (!checked) {
        const ok = await storage.setItem("device_check", "ok");
        if (!ok) throw new Error("Phone storage is unavailable, so offline answers cannot be protected. Free some space and retry.");
        await post(`/sets/${id}/preflight`, { preview: false, test_response: "25" });
        setChecked(true);
      }
      // Same start_key on every retry of this intent → no duplicate attempts.
      const a = await post(`/sets/${id}/start`, { start_key: key.current, device_checked: true, preview: false });
      await storage.removeItem(startKeyName);
      invalidate(`u.${user?.id}.`);
      router.replace((a.status === "completed" ? "/result/" : "/attempt/") + a.id as any);
    } catch (e: any) {
      setError(e.message);
      setBusy(false);
    }
  }
  async function toggleSave() {
    try {
      if (saved) await del(`/my/tests/saved/${id}`);
      else await post(`/my/tests/saved/${id}`, {});
      setSaved(!saved);
      invalidate(`u.${user?.id}.tests`);
    } catch (e: any) {
      setError(e.message);
    }
  }

  if (!s) return (
    <View style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <Header title="Loading paper…" onBack={() => router.back()} />
      <View style={{ padding: space.lg, gap: space.md }}>{error ? <ErrorBox error={error} retry={() => setReload((n) => n + 1)} /> : <><Skeleton h={140} /><Skeleton h={220} /></>}</View>
    </View>
  );
  const count = s.count ?? s.questions?.length;
  const minutes = s.rules?.minutes;
  const subj = s.chapter_subject;
  return (
    <View testID="set-detail-screen" style={{ flex: 1, backgroundColor: colors.surface, paddingTop: insets.top + space.sm }}>
      <Header title={s.title} eyebrow={`${s.exam} · ${s.series_id ? "All India series" : s.test_kind === "chapter" ? "Chapter practice" : s.test_kind === "pyq" ? "Previous-year paper" : "Full mock"}`} color={subjectColor(subj)} onBack={() => router.back()}
        right={<Press testID="set-save-toggle" onPress={toggleSave} accessibilityLabel={saved ? "Unsave paper" : "Save paper"} style={{ width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center", backgroundColor: colors.surfaceSecondary, borderWidth: 1, borderColor: colors.border }}><Icon name={saved ? "bookmark" : "bookmark-outline"} size={22} color={colors.custom_neonAmber} /></Press>} />
      <ScrollView contentContainerStyle={{ padding: space.lg, paddingTop: 0, paddingBottom: insets.bottom + space.xl, gap: space.md }}>
        <Card testID="set-facts" style={{ gap: space.md }}>
          <View style={{ flexDirection: "row", gap: space.sm }}>
            <Stat testID="set-question-count" label="Questions" value={count} />
            <Stat testID="set-duration" label={minutes ? "Minutes" : "Untimed"} value={minutes || "—"} />
            <Stat testID="set-maximum-marks" label="Max marks" value={s.maximum ?? count * s.rules.correct} />
          </View>
          <View testID="set-marking-rule" style={{ flexDirection: "row", gap: space.sm, flexWrap: "wrap" }}>
            {[[`+${s.rules.correct} correct`, colors.success], [`${s.rules.wrong} incorrect`, colors.error], [`${s.rules.skipped ?? 0} unanswered`, colors.muted]].map(([l, c]) => (
              <View key={l} style={{ paddingHorizontal: 10, paddingVertical: 4, borderRadius: radius.pill, borderWidth: 1, borderColor: c }}><T w="bold" size={12} color={c}>{l}</T></View>
            ))}
          </View>
          {s.types ? <T size={12} color={colors.muted}>{s.types.mcq ?? 0} MCQ · {s.types.integer ?? 0} integer</T> : null}
        </Card>
        <Card style={{ gap: space.sm }} testID="set-instructions">
          <T w="heavy" size={16}>Before you start</T>
          {[
            "One correct option per question, or an exact integer where stated. Mark for review and return anytime.",
            s.rules.numeric_rule,
            minutes ? "The timer starts when the attempt opens and keeps running if you disconnect or leave the app. Only answers the server receives before the deadline are scored." : "Untimed practice — come back to your saved attempt whenever you need.",
            s.series_id ? "Live results and solutions are sealed until 11:59 PM IST." : s.solution_kind === "answer_key_only" ? "Submitting is final. Score and supplied answer keys appear after grading. This book has no worked solutions." : "Submitting is final. Your result and supplied solutions appear afterwards.",
            s.test_kind === "chapter" ? "This is chapter practice, not a full exam simulation. Rank estimates are not shown for chapter scores." : null,
          ].filter(Boolean).map((x: any) => (
            <View key={x} style={{ flexDirection: "row", gap: 8 }}><Icon name="circle-small" size={20} color={colors.onSurface} /><T size={13} style={{ flex: 1 }}>{x}</T></View>
          ))}
          {s.source ? <T size={11} color={colors.muted}>{s.source}</T> : null}
        </Card>
        <Notice tone="info" icon="content-save-outline" testID="set-offline-notice">Your drafts stay on this phone if the internet drops. They show as Pending until the server confirms them — check the save status before submitting.</Notice>
        <ErrorBox error={error} testID="set-error" />
        {user ? (
          <>
            <Button testID="set-start-button" label={s.attempt?.status === "active" ? "Resume attempt" : "Start attempt"} icon="play" busy={busy} onPress={start} color={colors.surfaceInverse} />
            <T size={11} color={colors.muted} style={{ textAlign: "center" }}>By starting you accept the rules above. Your connection is checked automatically, and the clock starts only when the attempt opens.</T>
          </>
        ) : <Button testID="set-signin-button" label="Sign in to start" onPress={() => router.push("/entry")} />}
      </ScrollView>
    </View>
  );
}
