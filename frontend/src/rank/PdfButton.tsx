// "PDF lo" for any Rank list: one outline button, a spinner while the server draws it, then a one-line result.
import React, { useEffect, useState } from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { rankColors as colors } from "@/src/theme";
import { savePdf } from "./pdf";

export function PdfButton({ path, body, label, testID }: { path: string; body: unknown; label: string; testID: string }) {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  // A new score, filter or college means a new list: the old "taiyaar" line would look like this one was exported.
  const key = JSON.stringify(body);
  useEffect(() => { setMsg(null); }, [key]);
  const go = async () => {
    setBusy(true); setMsg(null);
    try { setMsg({ ok: true, text: `${await savePdf(path, body)} taiyaar` }); }
    catch (e: any) { setMsg({ ok: false, text: e?.message || "PDF nahi bani. Dobara try karo." }); }
    finally { setBusy(false); }
  };
  return <View style={styles.wrap}>
    <Pill testID={testID} label={label} icon="file-document-outline" busy={busy} onPress={go} bg={colors.custom_cardRaised} ink={colors.onSurface}
      style={styles.outline} accessibilityLabel={`${label}. Print karo, WhatsApp par bhejo ya phone mein save karo`} />
    <T testID={`${testID}-msg`} size={11.5} color={msg ? (msg.ok ? colors.success : colors.error) : colors.custom_dim}>
      {msg?.text ?? "Safed A4 PDF: print karo, WhatsApp par bhejo ya phone mein save karo."}
    </T>
  </View>;
}

const styles = StyleSheet.create({
  wrap: { gap: 6 },
  outline: { borderWidth: 1, borderColor: colors.custom_cardLineStrong },
});
