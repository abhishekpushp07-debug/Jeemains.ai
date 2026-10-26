import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { checkReadiness } from "@/src/api/readiness";
import { colors, space } from "@/src/theme";
import { Button, ErrorBox, Icon, Sheet, T } from "../ui";

export function ReadyToStart({ setId, title, busy, error, onStart, onClose }: {
  setId: string; title: string; busy: boolean; error?: string; onStart: (checkedAt: number) => void; onClose: () => void;
}) {
  const [checkedAt, setCheckedAt] = useState(0);
  const [failure, setFailure] = useState("");
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const ctl = new AbortController();
    checkReadiness(setId, ctl.signal).then(time => { if (!ctl.signal.aborted) setCheckedAt(time); }).catch(e => { if (!ctl.signal.aborted) setFailure(e.message); });
    return () => ctl.abort();
  }, [setId, retry]);
  return <Sheet visible onClose={() => { if (!busy) onClose(); }} testID="paper-ready-sheet">
    <View style={styles.top}><Icon name={checkedAt ? "check-circle-outline" : "school-outline"} size={34} color={checkedAt ? colors.success : colors.brandText} />
      <View style={styles.copy}><T testID="paper-ready-title" size={24} w="heavy">{checkedAt ? "Ready when you are." : "Getting you ready…"}</T><T testID="paper-ready-name" size={12} color={colors.muted} numberOfLines={2}>{title}</T></View>
    </View>
    <T testID="paper-ready-encouragement" size={15}>Take a deep breath. One question at a time. Give it your best.</T>
    <View style={styles.check}><Icon name="content-save-check-outline" size={20} color={checkedAt ? colors.success : colors.muted} /><T testID="paper-ready-device-status" size={13} color={colors.muted}>{checkedAt ? "Storage and connection checked" : failure ? "Check needs a retry" : "Checking device storage and connection"}</T>{!checkedAt && !failure ? <ActivityIndicator size="small" color={colors.brandText} /> : null}</View>
    <T testID="paper-ready-images-policy" size={12} color={colors.muted}>Original images unlock when the attempt starts. We then load the paper in the background, prioritising the question you open.</T>
    <T testID="paper-ready-timer-policy" size={12} w="bold" color={colors.brandText}>No countdown or forced wait. The exam timer starts only after Start now.</T>
    <ErrorBox testID="paper-ready-error" error={failure || error} retry={failure ? () => { setFailure(""); setCheckedAt(0); setRetry(n => n + 1); } : undefined} />
    <Button testID="paper-ready-start" label="Start now" icon="arrow-right" busy={busy} disabled={!checkedAt || !!failure} onPress={() => onStart(checkedAt)} />
    <Button testID="paper-ready-cancel" kind="secondary" label="Not now" disabled={busy} onPress={onClose} />
  </Sheet>;
}
const styles = StyleSheet.create({ top: { flexDirection: "row", gap: space.md, alignItems: "center" }, copy: { flex: 1 }, check: { flexDirection: "row", flexWrap: "wrap", alignItems: "center", gap: space.sm } });