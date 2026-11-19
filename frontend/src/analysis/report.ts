// The website draws the report PDF and the scorecard photo (so the app does not grow).
// The phone saves the file and opens WhatsApp or the share sheet; the browser downloads it.
import { Platform, Share } from "react-native";
import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { apiBytes } from "@/src/api/client";
import { sendFileToWhatsApp } from "@/src/whatsappFile";
import type { An } from "./format";

const IST = 19800; // the date in the file name is the Indian date, on every phone

export function reportName(an: An) {
  const day = new Date(((an.submitted_at || 0) + IST) * 1000).toISOString().slice(0, 10);
  const title = String(an.title || "Mock").replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 60) || "Mock";
  return `JEELIVE_${title}_${day}`;
}

function webSave(bytes: Uint8Array, name: string, type: string) {
  const url = URL.createObjectURL(new Blob([bytes as BlobPart], { type }));
  const a = (globalThis as any).document.createElement("a");
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}

function cacheFile(bytes: Uint8Array, name: string) {
  const file = new File(Paths.cache, name);
  if (file.exists) file.delete();
  file.write(bytes);
  return file;
}

/** The A4 analysis report. Returns a line to show the student ("" when the share sheet already said it all). */
export async function downloadReport(id: string, an: An): Promise<string> {
  const query = an.score_version && an.score_version !== "original" ? "?score_version=" + encodeURIComponent(an.score_version) : "";
  const bytes = await apiBytes(`/attempts/${id}/analysis/report.pdf${query}`);
  const name = reportName(an) + ".pdf";
  if (Platform.OS === "web") { webSave(bytes, name, "application/pdf"); return "Report download ho gayi."; }
  const file = cacheFile(bytes, name);
  if (!(await Sharing.isAvailableAsync())) throw new Error("Is phone par PDF save nahi ho paayi. Dobara try karo.");
  await Sharing.shareAsync(file.uri, { mimeType: "application/pdf", UTI: "com.adobe.pdf", dialogTitle: name });
  return "";
}

/** The scorecard photo (Score, Rank, Percentile; never the phone number) for WhatsApp. */
export async function shareScorecard(id: string, an: An): Promise<string> {
  const bytes = await apiBytes(`/attempts/${id}/analysis/share.png`);
  const name = reportName(an) + ".png", o = an.overview;
  const text = `Mera Score ${o.score}/${o.maximum} · JEELIVE.AI`;
  if (Platform.OS === "web") {
    const nav = (globalThis as any).navigator, WebFile = (globalThis as any).File;
    const file = WebFile ? new WebFile([bytes], name, { type: "image/png" }) : null;
    if (file && nav?.canShare?.({ files: [file] })) {
      try { await nav.share({ files: [file], title: an.title, text }); return ""; }
      catch (e: any) { if (e?.name === "AbortError") return ""; }
    }
    webSave(bytes, name, "image/png");
    return "Scorecard download ho gaya. Ab WhatsApp par bhej sakte ho.";
  }
  const file = cacheFile(bytes, name);
  if (await sendFileToWhatsApp({ url: file.uri, type: "image/png", filename: name, message: text })) return "";
  if (Platform.OS === "ios") { await Share.share({ url: file.uri, message: text }); return ""; }
  if (!(await Sharing.isAvailableAsync())) throw new Error("Is phone par scorecard share nahi ho paaya. Dobara try karo.");
  await Sharing.shareAsync(file.uri, { mimeType: "image/png", dialogTitle: "Scorecard share karo" });
  return "";
}
