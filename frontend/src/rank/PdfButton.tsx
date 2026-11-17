// PDF for any Rank list: a green "WhatsApp" (the file goes straight to a friend) and a "PDF" (save / print / any app),
// a spinner while the server draws it, then a one-line result.
import React, { useEffect, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { T } from "@/src/components/ui";
import { Pill } from "@/src/components/design";
import { rankColors as colors } from "@/src/theme";
import { savePdf, sendPdfWhatsApp, SentVia } from "./pdf";

const CAPTION = "📄 Meri college list, JEELIVE.AI (2026 ke official data par). Apni list free mein banao: https://jeelive.ai";
const SENT: Record<Exclude<SentVia, "cancelled">, (name: string) => string> = {
  whatsapp: () => "WhatsApp khul gaya, PDF attach hai: bas dost chuno aur bhejo",
  sheet: name => `${name} taiyaar: list mein WhatsApp chuno aur bhejo`,
  download: name => `${name} download hui. WhatsApp khul gaya: PDF attach karke bhejo`,
};

export function PdfButton({ path, body, label, testID }: { path: string; body: unknown; label: string; testID: string }) {
  const [busy, setBusy] = useState<"wa" | "pdf" | null>(null);
  const working = useRef(false); // two taps in the same instant must still make one PDF
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  // A new score, filter or college means a new list: the old "taiyaar" line would look like this one was exported.
  const key = JSON.stringify(body);
  useEffect(() => { setMsg(null); }, [key]);
  const run = async (kind: "wa" | "pdf") => {
    if (working.current) return;
    working.current = true;
    setBusy(kind); setMsg(null);
    try {
      if (kind === "wa") { const r = await sendPdfWhatsApp(path, body, CAPTION); setMsg(r.via === "cancelled" ? null : { ok: true, text: SENT[r.via](r.name) }); }
      else setMsg({ ok: true, text: `${await savePdf(path, body)} taiyaar` });
    } catch (e: any) { setMsg({ ok: false, text: e?.message || "PDF nahi bani. Dobara try karo." }); }
    finally { working.current = false; setBusy(null); }
  };
  return <View style={styles.wrap}>
    <View style={styles.row}>
      <Pill testID={`${testID}-whatsapp`} label="PDF WhatsApp" icon="whatsapp" busy={busy === "wa"} onPress={() => run("wa")} bg={colors.custom_whatsapp} ink={colors.custom_rankSparkle}
        style={styles.wa} accessibilityLabel={`${label} WhatsApp par dost ko bhejo`} />
      <Pill testID={testID} label={label} icon="file-document-outline" busy={busy === "pdf"} onPress={() => run("pdf")} bg={colors.custom_cardRaised} ink={colors.onSurface}
        style={styles.outline} accessibilityLabel={`${label}. Print karo ya phone mein save karo`} />
    </View>
    <T testID={`${testID}-msg`} size={11.5} color={msg ? (msg.ok ? colors.success : colors.error) : colors.custom_dim}>
      {msg?.text ?? "Safed A4 PDF: seedha WhatsApp par bhejo, print karo ya phone mein save karo."}
    </T>
  </View>;
}

const styles = StyleSheet.create({
  wrap: { gap: 6 },
  row: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  wa: { flexGrow: 1, flexBasis: 120 },
  outline: { flexGrow: 1, flexBasis: 140, borderWidth: 1, borderColor: colors.custom_cardLineStrong },
});
