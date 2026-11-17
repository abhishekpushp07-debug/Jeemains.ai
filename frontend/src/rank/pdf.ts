// White A4 PDFs of the Rank lists. The server draws them (so the app does not grow); the phone only saves the file
// and opens the share sheet (WhatsApp, Drive, Files, Print). On the web it downloads straight away.
import { Platform } from "react-native";
import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { BACKEND } from "@/src/api/client";

const FAIL = "PDF nahi bani. Network check karke dobara try karo.";

/** Builds the PDF on our server and hands it to the student. Returns the file name. */
export async function savePdf(path: string, body: unknown): Promise<string> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30000);
  let bytes: Uint8Array, name: string;
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
    name = /filename="([^"]+)"/.exec(res.headers.get("content-disposition") ?? "")?.[1] ?? "JEELIVE-Rank.pdf";
    bytes = new Uint8Array(await res.arrayBuffer().catch(() => { throw new Error(FAIL); }));
  } finally {
    clearTimeout(timer);
  }
  if (Platform.OS === "web") {
    const url = URL.createObjectURL(new Blob([bytes as BlobPart], { type: "application/pdf" }));
    const a = (globalThis as any).document.createElement("a");
    a.href = url; a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    return name;
  }
  const file = new File(Paths.cache, name);
  if (file.exists) file.delete();
  file.write(bytes);
  if (!(await Sharing.isAvailableAsync())) throw new Error("Is phone par PDF share nahi ho paayi. Dobara try karo.");
  await Sharing.shareAsync(file.uri, { mimeType: "application/pdf", UTI: "com.adobe.pdf", dialogTitle: name });
  return name;
}
