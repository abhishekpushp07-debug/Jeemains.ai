import React from "react";
import { useRouter } from "expo-router";
import { Button, Card, Notice, T } from "@/src/components/ui";
import { useTheme } from "@/src/theme";
import content from "@/src/legal/content.json";
import { LegalLayout, legalStyles } from "@/src/legal/LegalLayout";

export default function DeleteAccount() {
  const router = useRouter();
  const { colors } = useTheme();
  return <LegalLayout page="delete-account" title={content.deletion.title}>
    <Notice testID="delete-account-unavailable" tone="warning"><T testID="delete-account-status" size={15} w="bold" color={colors.warning}>{content.deletion.status}</T></Notice>
    <T testID="delete-account-explanation" size={16} style={legalStyles.body}>{content.deletion.explanation}</T>
    <Card testID="delete-account-scope-card" style={legalStyles.block}>
      <T testID="delete-account-scope-title" size={18} w="bold">One linked account, both services</T>
      <T testID="delete-account-scope" size={15} color={colors.muted} style={legalStyles.body}>{content.deletion.scope}</T>
    </Card>
    <T testID="delete-account-next-step" size={15} color={colors.muted} style={legalStyles.body}>{content.deletion.next}</T>
    <Button testID="delete-account-privacy" label="Read privacy policy" kind="secondary" icon="shield-check-outline" onPress={() => router.replace("/privacy")} />
  </LegalLayout>;
}