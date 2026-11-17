// Sharing a picture card (Mission card, Rank cards, shortlist card): the card's photo goes out with a short caption.
//   Android app build: WhatsApp opens with the photo and caption attached; the student only picks the friend.
//   iPhone: the share sheet gets the photo and caption (WhatsApp is in it).
//   Expo Go on Android / no WhatsApp: the share sheet gets the photo; the caption is copied to paste under it.
//   Phone browser: the browser's share sheet gets the photo and caption; where a browser cannot share photos, the text goes.
//   An older app build without the photo maker sends the full text (`fallback`) to WhatsApp instead.
import React from "react";
import { Platform, Share, View } from "react-native";
import * as Clipboard from "expo-clipboard";
import * as Sharing from "expo-sharing";
import { captureRef } from "react-native-view-shot";
import { sendWhatsApp } from "@/src/rapid/social";
import { sendFileToWhatsApp } from "@/src/whatsappFile";

export type CardRef = React.RefObject<React.ComponentRef<typeof View> | null>;
/** shared = false only when the student closed the share sheet without sending (where the phone tells us).
 *  away = the share went to another app or browser tab (WhatsApp), so the student comes back to us afterwards.
 *  note = something to show under the buttons ("" when nothing needs saying). */
export type ShareOutcome = { shared: boolean; away: boolean; note: string };
export type CardShare = { caption: string; filename: string; fallback?: string; toWhatsApp?: boolean; size?: { width: number; height: number } };

const PASTE = "Message copy ho gaya. WhatsApp mein photo ke neeche paste kar do.";

/** A PNG of the card on the phone, or null where it cannot be made (an older app build). Not for the web. */
export async function cardPhoto(card: CardRef, size?: CardShare["size"]): Promise<string | null> {
  try { return await captureRef(card, { format: "png", quality: 1, result: "tmpfile", ...size }); } catch { return null; }
}

/** The card as a browser File, or null where the browser cannot draw it. */
export async function cardWebFile(card: CardRef, filename: string): Promise<any | null> {
  try {
    const uri = await captureRef(card, { format: "png", result: "data-uri" });
    const blob = await (await fetch(uri)).blob();
    const WebFile = (globalThis as any).File;
    return WebFile ? new WebFile([blob], filename, { type: "image/png" }) : null;
  } catch { return null; }
}

export async function shareCard(card: CardRef, o: CardShare): Promise<ShareOutcome> {
  const text = o.fallback ?? o.caption;
  if (Platform.OS === "web") {
    const nav = (globalThis as any).navigator;
    const file = nav?.canShare ? await cardWebFile(card, o.filename) : null;
    if (file && nav.canShare({ files: [file] })) {
      try { await nav.share({ files: [file], text: o.caption }); return { shared: true, away: false, note: "" }; }
      catch (e: any) { if (e?.name === "AbortError") return { shared: false, away: false, note: "" }; }
    }
    if (o.toWhatsApp !== false) { await sendWhatsApp(text); return { shared: true, away: true, note: "" }; }
    try { await Share.share({ message: text }); return { shared: true, away: false, note: "" }; }
    catch (e: any) {
      if (e?.name === "AbortError") return { shared: false, away: false, note: "" };
      await Clipboard.setStringAsync(text);
      return { shared: true, away: false, note: "Message copy ho gaya. Kahin bhi paste karke bhej do." };
    }
  }
  const uri = await cardPhoto(card, o.size);
  if (!uri) { await sendWhatsApp(text); return { shared: true, away: true, note: "" }; }
  if (o.toWhatsApp !== false && await sendFileToWhatsApp({ url: uri, type: "image/png", filename: o.filename, message: o.caption })) return { shared: true, away: true, note: "" };
  if (Platform.OS === "ios") {
    const r = await Share.share({ url: uri, message: o.caption });
    return { shared: r.action !== Share.dismissedAction, away: false, note: "" };
  }
  await Clipboard.setStringAsync(o.caption);
  if (await Sharing.isAvailableAsync()) await Sharing.shareAsync(uri, { mimeType: "image/png", dialogTitle: "Please share karo" });
  else await sendWhatsApp(text);
  return { shared: true, away: true, note: PASTE };
}
