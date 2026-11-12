import React from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { useTheme } from "@/src/theme";
import content from "@/src/legal/content.json";
import { LegalLayout, legalStyles } from "@/src/legal/LegalLayout";

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
    <Pill testID="privacy-account-deletion" label="Account deletion information" kind="outline" icon="account-remove-outline" onPress={() => router.push("/delete-account")} />
  </LegalLayout>;
}