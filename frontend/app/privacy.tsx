import React from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { useTheme } from "@/src/theme";
import content from "@/src/legal/content.json";
import { LegalLayout, legalStyles } from "@/src/legal/LegalLayout";
import { ANALYTICS_NOTICE } from "@/src/AnalyticsSwitch";

export default function Privacy() {
  const router = useRouter();
  const { colors } = useTheme();
  return <LegalLayout page="privacy" title={content.privacyTitle}>
    <T testID="privacy-version" size={12} color={colors.muted}>Updated {content.version} · Available without signing in</T>
    <T testID="privacy-intro" size={16} style={legalStyles.body}>{content.intro}</T>
    {content.sections.map(section => <View key={section.id} testID={`privacy-section-${section.id}`} style={legalStyles.block}>
      <T testID={`privacy-heading-${section.id}`} w="heavy" size={11} color={colors.custom_eyebrow} style={{ letterSpacing: 2.2 }}>{section.title.toUpperCase()}</T>
      <T testID={`privacy-body-${section.id}`} size={15} color={colors.muted} style={legalStyles.body}>{section.body}</T>
    </View>)}
    <View testID="privacy-section-analytics" style={legalStyles.block}>
      <T testID="privacy-heading-analytics" w="heavy" size={11} color={colors.custom_eyebrow} style={{ letterSpacing: 2.2 }}>USAGE ANALYTICS</T>
      <T testID="privacy-body-analytics" size={15} color={colors.muted} style={legalStyles.body}>{ANALYTICS_NOTICE}</T>
    </View>
    <Pill testID="privacy-account-deletion" label="Delete account" kind="outline" icon="account-remove-outline" onPress={() => router.push("/delete-account")} />
  </LegalLayout>;
}