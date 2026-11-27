// "Naam badlo": the one name the student is shown by everywhere: every leaderboard, Compare, their report and Rapid Fire.
// It is written from the pink Rank card and from the Account screen. Same rule and same words as the website's own form
// (PUT /profile/display-name): 2 to 20 letters, digits or spaces, changed at most 3 times a day; an empty name takes it
// away, and the student is "Learner" + a code again.
// The website checks the name and its answer is shown as it is; the app never keeps a name of its own.
import React, { useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { put } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { nameSaved } from "@/src/profileName";
import { Notice, T } from "@/src/components/ui";
import { DSheet, Pill } from "@/src/components/design";
import { colors, fonts, noOutline, space } from "@/src/theme";

const clean = (name: string) => name.trim().replace(/\s+/g, " ");

/** `current` = the name shown now ("" = none); `onSaved` gets the name the website kept ("" = taken away). */
export function NameSheet({ visible, current, onClose, onSaved }: { visible: boolean; current: string; onClose: () => void; onSaved: (name: string) => void }) {
  return <DSheet visible={visible} onClose={onClose} testID="aits-name-sheet" title="Aapka naam" keyboard>
    <NameForm current={current} onClose={onClose} onSaved={onSaved} />
  </DSheet>;
}

// Drawn only while the sheet is open, so every opening starts from the name shown now.
function NameForm({ current, onClose, onSaved }: { current: string; onClose: () => void; onSaved: (name: string) => void }) {
  const { user } = useAuth();
  const [text, setText] = useState(current);
  const [busy, setBusy] = useState<"" | "save" | "remove">("");
  const [error, setError] = useState("");
  const send = async (name: string) => {
    setError(""); setBusy(name ? "save" : "remove");
    try {
      const kept = (await put<{ display_name?: string | null }>("/profile/display-name", { name }))?.display_name || "";
      if (user) nameSaved(user.id, kept); // leaderboards and Rapid Fire ask again and show it
      onSaved(kept);
    } catch (e: any) {
      setError(e?.message || "Naam save nahi ho paaya. Internet dekh kar dobara try karo.");
      setBusy("");
    }
  };
  const save = () => {
    if (busy) return;
    const name = clean(text);
    if (!name) setError(current ? 'Naam likho, ya "Naam hatao" dabao.' : "Pehle apna naam likho.");
    else send(name);
  };
  return <>
    <T testID="aits-name-about" size={13} color={colors.custom_softText}>Leaderboard, Compare, aapki report aur Rapid Fire mein “Learner” aur code ki jagah yeh naam dikhega. Aapka phone number kabhi nahi dikhta. Naam din mein 3 baar badal sakte ho.</T>
    {error ? <Notice testID="aits-name-error" tone="error">{error}</Notice> : null}
    <View style={styles.field}>
      <T w="bold" size={12} color={colors.custom_eyebrow}>Aapka naam</T>
      <TextInput testID="aits-name-input" value={text} onChangeText={t => { setText(t); setError(""); }} maxLength={20} autoFocus autoCapitalize="words" autoCorrect={false}
        autoComplete="nickname" returnKeyType="done" onSubmitEditing={save} editable={!busy} placeholder="Jaise: Arjun Sharma" placeholderTextColor={colors.custom_dim}
        accessibilityLabel="Aapka naam" style={[styles.input, noOutline]} />
      <T testID="aits-name-hint" size={11.5} color={colors.custom_eyebrow}>2 se 20 akshar, ank ya space · {clean(text).length}/20</T>
    </View>
    <Pill testID="aits-name-save" size="lg" icon="check" label="Naam save karo" busy={busy === "save"} disabled={!!busy} onPress={save} />
    <View style={styles.row}>
      {current ? <Pill testID="aits-name-remove" kind="danger" label="Naam hatao" busy={busy === "remove"} disabled={!!busy} onPress={() => send("")} style={styles.half} /> : null}
      <Pill testID="aits-name-cancel" kind="outline" label="Rehne do" disabled={!!busy} onPress={onClose} style={styles.half} />
    </View>
  </>;
}

const styles = StyleSheet.create({
  field: { gap: 6 },
  input: { minHeight: 52, borderRadius: 16, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_cardRaised, paddingHorizontal: space.lg,
    fontFamily: fonts.bold, fontSize: 17, color: colors.onSurface },
  row: { flexDirection: "row", gap: space.sm },
  half: { flex: 1, minWidth: 0 },
});
