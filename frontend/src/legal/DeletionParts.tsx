import React from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { DCard, IconCircle, Pill } from "@/src/components/design";
import { Glyph } from "@/src/components/Glyph";
import { space, useTheme } from "@/src/theme";
import type { DeletionReceipt } from "@/src/api/client";
import content from "./content.json";

const longDate = (iso: string) => new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });

/** What happens to each part of the account, before anything is asked. */
export function DeletionSteps() {
  const { colors } = useTheme();
  return <View testID="delete-account-steps" style={styles.steps}>
    {content.deletion.steps.map(step => <View key={step.id} testID={`delete-account-step-${step.id}`} style={styles.step}>
      <IconCircle icon={step.icon as any} color={colors.onSurface} size={40} />
      <View style={styles.stepText}>
        <T testID={`delete-account-step-${step.id}-title`} w="bold" size={15}>{step.title}</T>
        <T size={13.5} color={colors.muted} style={styles.body}>{step.body}</T>
      </View>
    </View>)}
  </View>;
}

function ReceiptRow({ icon, label, value, tone, testID }: { icon: string; label: string; value: string; tone: string; testID: string }) {
  const { colors } = useTheme();
  return <View testID={testID} style={styles.receiptRow}>
    <Glyph name={icon as any} size={20} color={tone} stroke={1.8} />
    <T size={14} color={colors.muted} style={styles.flex}>{label}</T>
    <T testID={`${testID}-value`} w="bold" size={14} color={tone}>{value}</T>
  </View>;
}

/** After the request: the number to keep, and where each part stands. */
export function DeletionDone({ receipt, onDone }: { receipt: DeletionReceipt; onDone: () => void }) {
  const { colors } = useTheme();
  return <View testID="delete-account-done" style={styles.steps} accessibilityLiveRegion="polite">
    <View style={styles.doneHead}>
      <IconCircle icon="check" color={colors.success} bg={colors.custom_successSoft} line={colors.success} size={56} />
      <T testID="delete-account-done-title" accessibilityRole="header" w="heavy" size={24}>Your account is being deleted</T>
      <T size={14.5} color={colors.muted} style={styles.body}>You are signed out. Keep the request number below if you ever need to ask about it.</T>
    </View>
    <DCard testID="delete-account-receipt" style={styles.receipt}>
      <T size={11} w="heavy" color={colors.custom_eyebrow} style={styles.eyebrow}>REQUEST NUMBER</T>
      <T testID="delete-account-request-id" selectable w="heavy" size={26} style={styles.code}>{receipt.request_id}</T>
      <ReceiptRow testID="delete-account-receipt-rapid" icon="lightning-bolt" label="Rapid Fire data" value={receipt.rapid_fire_erased ? "Deleted" : "Deleting"} tone={colors.success} />
      <ReceiptRow testID="delete-account-receipt-website" icon="web" label="Website account"
        value={receipt.website_account === "deleted" ? "Deleted" : `By ${longDate(receipt.due_at)}`} tone={receipt.website_account === "deleted" ? colors.success : colors.warning} />
      <ReceiptRow testID="delete-account-receipt-device" icon="logout" label="This device" value="Signed out" tone={colors.success} />
    </DCard>
    <Pill testID="delete-account-done-button" size="lg" label="Done" onPress={onDone} />
  </View>;
}

const styles = StyleSheet.create({
  steps: { gap: space.lg },
  step: { flexDirection: "row", gap: space.md, alignItems: "flex-start" },
  stepText: { flex: 1, gap: 2 },
  body: { lineHeight: 21 },
  flex: { flex: 1 },
  doneHead: { gap: space.sm, alignItems: "flex-start" },
  receipt: { gap: space.md, padding: 20 },
  receiptRow: { flexDirection: "row", alignItems: "center", gap: space.sm, minHeight: 32 },
  eyebrow: { letterSpacing: 2.2 },
  code: { letterSpacing: 2, fontVariant: ["tabular-nums"] },
});
