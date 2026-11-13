import React, { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, TextInput, View } from "react-native";
import * as Clipboard from "expo-clipboard";
import { rf } from "@/src/api/client";
import { invalidate } from "@/src/useCached";
import { Icon, T } from "@/src/components/ui";
import { arena } from "@/src/theme";
import { CloseButton, Panel, RaisedButton, arenaInput } from "./arena";
import { Pop } from "./juice";
import { PersonRow } from "./parts";
import { ErrorBox } from "./ui";
import { PlayerCard, cleanCode, prettyCode, seenText, shareFriendCode, useFriendCode } from "./social";

type Found = PlayerCard & { is_me: boolean; friend: boolean };

/** Friends are made only with a Friend Code: yours to share, and a box for a friend's. One add makes both of you friends. */
export function FriendCodeBox({ uid, onAdded, onOpen }: { uid: string; onAdded: () => void; onOpen: (pid: string) => void }) {
  const mine = useFriendCode(uid);
  const [text, setText] = useState(""), [found, setFound] = useState<Found | null>(null);
  const [busy, setBusy] = useState<"" | "find" | "add">(""), [error, setError] = useState(""), [copied, setCopied] = useState(false);
  const code = cleanCode(text), my = mine.data?.code || "";

  // A complete code (8 letters and digits) is looked up by itself; the player is shown before anything is added.
  useEffect(() => {
    setFound(null); setError("");
    if (code.length !== 8) { setBusy(""); return; }
    let live = true;
    setBusy("find");
    rf<Found>(`/friends/code/${code}`, uid).then((p) => { if (live) setFound(p); }).catch((e) => { if (live) setError(e.message); }).finally(() => { if (live) setBusy(""); });
    return () => { live = false; };
  }, [code, uid]);

  const add = async () => {
    setBusy("add"); setError("");
    try {
      await rf("/friends", uid, { method: "POST", body: { code } });
      invalidate(`u.${uid}.rffriends`);
      setFound((p) => (p ? { ...p, friend: true } : p));
      onAdded();
    } catch (e: any) { setError(e.message); }
    finally { setBusy(""); }
  };

  return <View style={styles.box}>
    <Panel gold testID="rf-my-code" style={styles.mine}>
      <View style={styles.flex}>
        <T w="heavy" size={11} color={arena.aqua} style={styles.spaced}>YOUR FRIEND CODE</T>
        {my ? <T testID="rf-my-code-text" w="heavy" size={26} color={arena.gold} numberOfLines={1} adjustsFontSizeToFit style={styles.code}>{prettyCode(my)}</T>
          : mine.error ? <T testID="rf-my-code-error" size={12} color={arena.danger} onPress={mine.reload}>Could not load. Tap to retry.</T> : <ActivityIndicator testID="rf-my-code-loading" color={arena.aqua} style={styles.loading} />}
      </View>
      <RaisedButton testID="rf-my-code-copy" tone="wine" height={44} disabled={!my} accessibilityLabel={copied ? "Friend Code copied" : "Copy your Friend Code"} style={styles.key}
        onPress={async () => { await Clipboard.setStringAsync(my); setCopied(true); }}><Icon name={copied ? "check" : "content-copy"} size={20} color={arena.text} /></RaisedButton>
      <RaisedButton testID="rf-my-code-share" height={44} disabled={!my} accessibilityLabel="Share your Friend Code on WhatsApp" style={styles.key} onPress={() => shareFriendCode(my)}><Icon name="whatsapp" size={22} color={arena.text} /></RaisedButton>
    </Panel>

    <View style={styles.entry}>
      <Icon name="account-plus" size={22} color={arena.aqua} />
      <TextInput testID="rf-code-input" accessibilityLabel="Enter a friend’s Friend Code" value={text} onChangeText={(v) => setText(v.toUpperCase())} placeholder="Enter a friend’s code" placeholderTextColor={arena.faint}
        autoCapitalize="characters" autoCorrect={false} maxLength={12} style={styles.input} />
      {busy === "find" ? <ActivityIndicator testID="rf-code-finding" color={arena.aqua} style={styles.finding} /> : text ? <CloseButton testID="rf-code-clear" label="Clear code" onPress={() => setText("")} /> : null}
    </View>
    <ErrorBox testID="rf-code-error" error={error} />
    {found ? <Pop><PersonRow testID="rf-code-found" p={found} sub={`Level ${found.level} · ${seenText(found)}`} selected onPress={found.is_me ? undefined : () => onOpen(found.pid)}
      right={found.is_me ? <T testID="rf-code-me" w="heavy" size={12} color={arena.aqua}>That’s you</T>
        : found.friend ? <T testID="rf-code-friend" w="heavy" size={12} color={arena.gold}>Friends ✓</T>
        : <RaisedButton testID="rf-code-add" label="Add" height={42} busy={busy === "add"} disabled={!!busy} onPress={add} style={styles.add} />} /></Pop>
      : !text ? <T testID="rf-code-hint" size={12} color={arena.muted} style={styles.center}>Friends are made only with a Friend Code. Share yours or enter a friend’s, and you both become friends at once.</T> : null}
  </View>;
}

const styles = StyleSheet.create({
  flex: { flex: 1, minWidth: 0 }, center: { textAlign: "center" }, box: { gap: 8 }, spaced: { letterSpacing: 2 },
  mine: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 10, paddingHorizontal: 12 },
  code: { letterSpacing: 4 }, loading: { alignSelf: "flex-start", height: 34 }, key: { width: 48 }, add: { width: 76 }, finding: { marginRight: 12 },
  entry: { flexDirection: "row", alignItems: "center", gap: 8, minHeight: 54, paddingLeft: 14, paddingRight: 6, borderRadius: 18, backgroundColor: arena.panelEdge, borderWidth: 1.5, borderColor: arena.rim },
  input: { ...arenaInput, flex: 1, height: 50, borderWidth: 0, paddingHorizontal: 0, backgroundColor: arena.clear, fontSize: 16, letterSpacing: 2 },
});
