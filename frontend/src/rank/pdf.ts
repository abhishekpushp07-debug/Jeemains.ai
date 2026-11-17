// White A4 PDFs of the Rank lists. The server draws them (so the app does not grow); the phone saves the file and
// either opens the share sheet (Drive, Files, Print...) or goes straight into WhatsApp with the file attached.
import { Platform } from "react-native";
import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { BACKEND } from "@/src/api/client";
import { sendWhatsApp } from "@/src/rapid/social";
import { sendFileToWhatsApp } from "@/src/whatsappFile";
import { CardRef, cardPhoto, cardWebFile } from "@/src/shareCard";

const FAIL = "PDF nahi bani. Network check karke dobara try karo.";
const PHOTO = "JEELIVE-Rank-Card.png";
type Pdf = { name: string; bytes: Uint8Array };

async function fetchPdf(path: string, body: unknown): Promise<Pdf> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30000);
  try {
    let res: Response;
    try {
      res = await fetch(`${BACKEND}/api/rank/pdf${path}`, {
        method: "POST", signal: ctrl.signal, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
    } catch (e: any) {
      throw new Error(e?.name === "AbortError" ? "Network kamzor hai. Dobara try karo." : FAIL);
    }
    if (!res.ok) {
      const d = await res.json().catch(() => null);
      throw new Error(typeof d?.detail === "string" ? d.detail : FAIL);
    }
    const name = /filename="([^"]+)"/.exec(res.headers.get("content-disposition") ?? "")?.[1] ?? "JEELIVE-Rank.pdf";
    return { name, bytes: new Uint8Array(await res.arrayBuffer().catch(() => { throw new Error(FAIL); })) };
  } finally {
    clearTimeout(timer);
  }
}

function webDownload({ name, bytes }: Pdf) {
  const url = URL.createObjectURL(new Blob([bytes as BlobPart], { type: "application/pdf" }));
  const a = (globalThis as any).document.createElement("a");
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}

function cacheFile({ name, bytes }: Pdf) {
  const file = new File(Paths.cache, name);
  if (file.exists) file.delete();
  file.write(bytes);
  return file;
}

async function shareSheet(file: File, name: string) {
  if (!(await Sharing.isAvailableAsync())) throw new Error("Is phone par PDF share nahi ho paayi. Dobara try karo.");
  await Sharing.shareAsync(file.uri, { mimeType: "application/pdf", UTI: "com.adobe.pdf", dialogTitle: name });
}

/** "PDF" button: the web downloads it, a phone opens the share sheet. Returns the file name. */
export async function savePdf(path: string, body: unknown): Promise<string> {
  const pdf = await fetchPdf(path, body);
  if (Platform.OS === "web") webDownload(pdf);
  else await shareSheet(cacheFile(pdf), pdf.name);
  return pdf.name;
}

export type SentVia = "whatsapp" | "both" | "sheet" | "download" | "cancelled";

/** "WhatsApp" button: the PDF file itself goes to a friend, with the photo of `card` (the Rank card) where possible.
 *  Android app: WhatsApp opens with the card photo and the PDF attached, the student only picks the friend.
 *  iPhone / Expo Go: iOS lets no app open WhatsApp with a file, so the share sheet opens with the PDF (WhatsApp is in it).
 *  Web: a phone browser shares the photo and the PDF; a computer downloads the PDF and opens WhatsApp with the message. */
export async function sendPdfWhatsApp(path: string, body: unknown, caption: string, card?: CardRef): Promise<{ name: string; via: SentVia }> {
  const pdf = await fetchPdf(path, body);
  if (Platform.OS === "web") {
    const nav = (globalThis as any).navigator, WebFile = (globalThis as any).File;
    const doc = WebFile ? new WebFile([pdf.bytes], pdf.name, { type: "application/pdf" }) : null;
    const photo = doc && card && nav?.canShare ? await cardWebFile(card, PHOTO) : null;
    for (const files of [photo ? [photo, doc] : null, doc ? [doc] : null]) {
      if (!files || !nav?.canShare?.({ files })) continue;
      try { await nav.share({ files, text: caption }); return { name: pdf.name, via: "sheet" }; }
      catch (e: any) { if (e?.name === "AbortError") return { name: pdf.name, via: "cancelled" }; }
    }
    webDownload(pdf);
    await sendWhatsApp(caption);
    return { name: pdf.name, via: "download" };
  }
  const file = cacheFile(pdf);
  const photo = card ? await cardPhoto(card) : null;
  if (photo && await sendFileToWhatsApp({ urls: [photo, file.uri], filenames: [PHOTO, pdf.name], message: caption })) return { name: pdf.name, via: "both" };
  if (await sendFileToWhatsApp({ url: file.uri, type: "application/pdf", filename: pdf.name, message: caption })) return { name: pdf.name, via: "whatsapp" };
  await shareSheet(file, pdf.name); // WhatsApp missing or refused: the share sheet still gets the file out
  return { name: pdf.name, via: "sheet" };
}
