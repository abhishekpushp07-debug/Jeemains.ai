import React from "react";
import { View } from "react-native";
import { useRouter } from "expo-router";
import { Button, T } from "@/src/components/ui";
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
      <T testID={`privacy-heading-${section.id}`} w="bold" size={19}>{section.title}</T>
      <T testID={`privacy-body-${section.id}`} size={15} color={colors.muted} style={legalStyles.body}>{section.body}</T>
    </View>)}
    <Button testID="privacy-account-deletion" label="Account deletion information" kind="secondary" icon="account-remove-outline" onPress={() => router.push("/delete-account")} />
  </LegalLayout>;
}