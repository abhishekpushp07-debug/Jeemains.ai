import React, { useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useRouter } from "expo-router";
import { T } from "@/src/components/ui";
import { Pill, ScreenHeader } from "@/src/components/design";
import { space, useTheme } from "@/src/theme";
import { contactPrivacy, openLegal, privacyContact } from "./links";

export function LegalLayout({ page, title, children }: { page: "privacy" | "delete-account"; title: string; children: React.ReactNode }) {
  const insets = useSafeAreaInsets(), router = useRouter();
  const { colors } = useTheme();
  const [error, setError] = useState("");
  const open = async (action: () => Promise<void>, message: string) => { setError(""); try { await action(); } catch { setError(message); } };
  return <View testID={`${page}-screen`} style={[styles.screen, { paddingTop: insets.top, backgroundColor: colors.surface }]}>
    <ScreenHeader title={title} eyebrow="Privacy" testID={`${page}-header`} backTestID={`${page}-back`} onBack={() => router.canGoBack() ? router.back() : router.replace("/entry")} />
    <ScrollView contentContainerStyle={[styles.content, { paddingBottom: insets.bottom + space.xxl }]}>
      {children}
      <Pill testID={`${page}-public-page`} label="Open public web page" kind="outline" icon="open-in-new" onPress={() => void open(() => openLegal(page), "Couldn't open the public page. Check your connection and try again.")} />
      <Pill testID={`${page}-contact`} label="Contact privacy support" kind="outline" icon="email-outline" onPress={() => void open(contactPrivacy, `No email app could be opened. You can contact ${privacyContact}. Never include your PIN.`)} />
      <T testID={`${page}-contact-email`} selectable size={14} color={colors.brandText}>{privacyContact}</T>
      <T testID={`${page}-contact-note`} size={12} color={colors.muted}>Opens your email app. No message is sent automatically. Never email your PIN.</T>
      {error ? <T testID={`${page}-link-error`} accessibilityRole="alert" size={13} color={colors.error}>{error}</T> : null}
    </ScrollView>
  </View>;
}
export const legalStyles = StyleSheet.create({ block: { gap: space.sm }, body: { lineHeight: 24 } });
const styles = StyleSheet.create({ screen: { flex: 1 }, content: { padding: space.lg, gap: space.xl } });