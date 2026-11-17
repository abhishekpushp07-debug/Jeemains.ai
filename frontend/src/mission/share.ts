// Sharing the Mission card. The picture of the card goes out with the caption and the student's own link:
//   Android app build: WhatsApp opens with the picture and caption attached, the student only picks the friend.
//   iPhone: the share sheet gets the picture and caption (WhatsApp is in it).
//   Expo Go on Android: the share sheet gets the picture; the caption is copied to paste under it.
//   Web: WhatsApp (or the share sheet) gets the caption with the link.
import React from "react";
import { AppState, Platform, Share, View } from "react-native";
import * as Clipboard from "expo-clipboard";
import * as Sharing from "expo-sharing";
import { captureRef } from "react-native-view-shot";
import { sendWhatsApp } from "@/src/rapid/social";
import { sendFileToWhatsApp } from "@/src/whatsappFile";

/** shared = false only when the student closed the share sheet without sending (where the phone tells us).
 *  away = the share went to another app or browser tab (WhatsApp), so the student comes back to us afterwards.
 *  note = something to show under the buttons ("" when nothing needs saying). */
export type ShareOutcome = { shared: boolean; away: boolean; note: string };

export async function shareMission(card: React.RefObject<React.ComponentRef<typeof View> | null>, toWhatsApp: boolean, caption: string): Promise<ShareOutcome> {
  if (Platform.OS === "web") {
    if (toWhatsApp) { await sendWhatsApp(caption); return { shared: true, away: true, note: "" }; }
    try { await Share.share({ message: caption }); return { shared: true, away: false, note: "" }; }
    catch (e: any) {
      if (e?.name === "AbortError") return { shared: false, away: false, note: "" }; // closed the share sheet
      await Clipboard.setStringAsync(caption); // browsers without a share sheet
      return { shared: true, away: false, note: "Message copy ho gaya. Kahin bhi paste karke bhej do." };
    }
  }
  const uri = await captureRef(card, { format: "png", quality: 1, result: "tmpfile", width: 1080, height: 1350 });
  if (toWhatsApp && await sendFileToWhatsApp({ url: uri, type: "image/png", filename: "JEELIVE-Mission.png", message: caption })) return { shared: true, away: true, note: "" };
  if (Platform.OS === "ios") {
    const r = await Share.share({ url: uri, message: caption });
    return { shared: r.action !== Share.dismissedAction, away: false, note: "" };
  }
  await Clipboard.setStringAsync(caption);
  if (await Sharing.isAvailableAsync()) await Sharing.shareAsync(uri, { mimeType: "image/png", dialogTitle: "Please share karo" });
  else await sendWhatsApp(caption);
  return { shared: true, away: true, note: "Message copy ho gaya. WhatsApp mein photo ke neeche paste kar do." };
}

/** Watches the trip to WhatsApp: start it before sharing. `back()` resolves once the student has left the app and
 *  come back. A phone cannot tell us whether the message was really sent, so coming back is the signal. If the app
 *  never leaves within 3 seconds (WhatsApp opened in a window on a computer, a blocked pop-up), it resolves then. */
export function watchReturn() {
  let left = false, wake = () => {}, timer: ReturnType<typeof setTimeout> | undefined;
  const sub = AppState.addEventListener("change", s => {
    if (s !== "active") { left = true; clearTimeout(timer); }
    else if (left) wake();
  });
  return {
    back: () => new Promise<void>(done => {
      wake = done;
      if (!left) timer = setTimeout(done, 3000);
      else if (AppState.currentState === "active") done(); // already back (the share sheet returned with us)
    }),
    stop: () => { clearTimeout(timer); sub.remove(); },
  };
}
