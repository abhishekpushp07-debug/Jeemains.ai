import React, { useState } from "react";
import { StyleSheet, TextInput, View } from "react-native";
import { put } from "@/src/api/client";
import { Icon, T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { colors, fonts, noOutline, space } from "@/src/theme";
import { An, TONE } from "./format";
import { Block } from "./parts";

const HINTS = ["Jaise: Easy sawaal pehle round mein hi pakke karunga", "Jaise: 50% se kam yakeen ho to jawab nahi dunga", "Jaise: Ek sawaal par Par time ke 2 guna se zyada nahi"];

/** "Is test se meri 3 seekh": private to the student, printed in the report and shown again on the next mock's analysis. */
export function Learnings({ id, an }: { id: string; an: An }) {
  const l = an.learnings || { mine: [], previous: null };
  const [items, setItems] = useState<string[]>(() => [0, 1, 2].map(i => l.mine[i] || ""));
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(l.mine.length > 0);
  const [note, setNote] = useState<{ ok: boolean; text: string } | null>(null);
  const change = (i: number, v: string) => { setSaved(false); setNote(null); setItems(old => old.map((x, k) => (k === i ? v.slice(0, 140) : x))); };
  const save = async () => {
    setBusy(true); setNote(null);
    try {
      const r = await put<{ items: string[] }>(`/attempts/${id}/learnings`, { items: items.map(x => x.trim()).filter(Boolean) });
      setItems([0, 1, 2].map(i => r.items[i] || ""));
      setSaved(true);
      setNote({ ok: true, text: "3 seekh save ho gayi. Agle mock ke analysis mein yeh dobara dikhengi." });
    } catch (e: any) { setNote({ ok: false, text: e?.message || "Save nahi ho paaya. Dobara try karo." }); }
    setBusy(false);
  };
  const prev = l.previous;
  return <Block id="learnings" kicker="SIRF AAPKE LIYE" title="Is test se meri 3 seekh" note="Apne shabdon mein likho. Report PDF mein bhi aayengi aur agle mock par yaad dilayi jaayengi.">
    {prev ? <View testID="a2-learnings-previous" style={styles.prev}>
      <Icon name="history" size={18} color={TONE.info.ink} />
      <View style={{ flex: 1, gap: 4 }}>
        <T w="heavy" size={13}>Pichhle mock ({prev.title || "mock"}) mein aapne likha tha:</T>
        {prev.items.map((x: string, i: number) => <T key={i} size={13} color={colors.custom_softText}>{i + 1}. {x}</T>)}
        <T size={11.5} color={colors.muted}>Kya is baar inpar amal hua? Neeche ke hisaab se khud check karo.</T>
      </View>
    </View> : null}
    {items.map((v, i) => <View key={i} style={styles.note}>
      <View style={styles.no}><T w="heavy" size={13} color={colors.custom_softText}>{i + 1}</T></View>
      <TextInput testID={"a2-learning-input-" + i} value={v} maxLength={140} multiline placeholder={HINTS[i]} placeholderTextColor={colors.custom_dim} onChangeText={t => change(i, t)}
        accessibilityLabel={"Seekh " + (i + 1)} style={[styles.input, noOutline]} />
    </View>)}
    <View style={styles.row}>
      <Pill testID="a2-learnings-save" kind={saved ? "outline" : "light"} size="sm" icon={saved ? "check" : "notebook-edit-outline"} label={saved ? "Saved" : "Save karo"} busy={busy} disabled={saved} onPress={save} />
      <T size={11.5} color={colors.muted} style={{ flex: 1 }}>Yeh sirf aap dekh sakte ho.</T>
    </View>
    {note ? <T testID="a2-learnings-note" size={12.5} color={note.ok ? colors.success : colors.error}>{note.text}</T> : null}
  </Block>;
}

const styles = StyleSheet.create({
  prev: { flexDirection: "row", gap: space.md, padding: space.md, borderRadius: 16, backgroundColor: TONE.info.soft, borderWidth: 1, borderColor: TONE.info.line },
  note: { flexDirection: "row", alignItems: "flex-start", gap: space.sm },
  no: { width: 30, height: 30, marginTop: 9, borderRadius: 15, backgroundColor: colors.custom_cardRaised, borderWidth: 1, borderColor: colors.custom_cardLine, alignItems: "center", justifyContent: "center" },
  input: { flex: 1, minHeight: 48, borderRadius: 14, borderWidth: 1, borderColor: colors.custom_cardLineStrong, backgroundColor: colors.custom_card, paddingHorizontal: space.md, paddingVertical: 12, fontFamily: fonts.medium, fontSize: 14, color: colors.onSurface, textAlignVertical: "top" },
  row: { flexDirection: "row", alignItems: "center", gap: space.md },
});
