// Sharing the Mission card. The picture of the card goes out with the caption and the app link:
//   Android app build: WhatsApp opens with the picture and caption attached, the student only picks the friend.
//   iPhone: the share sheet gets the picture and caption (WhatsApp is in it).
//   Expo Go on Android: the share sheet gets the picture; the caption is copied to paste under it.
//   Web: WhatsApp (or the share sheet) gets the caption with the link.
import React from "react";
import { Platform, Share, View } from "react-native";
import * as Clipboard from "expo-clipboard";
import * as Sharing from "expo-sharing";
import { captureRef } from "react-native-view-shot";
import { sendWhatsApp } from "@/src/rapid/social";
import { sendFileToWhatsApp } from "@/src/whatsappFile";
import { CAPTION } from "./copy";

/** shared = false only when the student closed the share sheet without sending (where the phone tells us).
 *  note = something to show under the buttons ("" when nothing needs saying). */
export type ShareOutcome = { shared: boolean; note: string };

export async function shareMission(card: React.RefObject<React.ComponentRef<typeof View> | null>, toWhatsApp: boolean): Promise<ShareOutcome> {
  if (Platform.OS === "web") {
    if (toWhatsApp) { await sendWhatsApp(CAPTION); return { shared: true, note: "" }; }
    try { await Share.share({ message: CAPTION }); return { shared: true, note: "" }; }
    catch (e: any) {
      if (e?.name === "AbortError") return { shared: false, note: "" }; // closed the share sheet
      await Clipboard.setStringAsync(CAPTION); // browsers without a share sheet
      return { shared: true, note: "Message copy ho gaya. Kahin bhi paste karke bhej do." };
    }
  }
  const uri = await captureRef(card, { format: "png", quality: 1, result: "tmpfile", width: 1080, height: 1350 });
  if (toWhatsApp && await sendFileToWhatsApp({ url: uri, type: "image/png", filename: "JEELIVE-Mission.png", message: CAPTION })) return { shared: true, note: "" };
  if (Platform.OS === "ios") {
    const r = await Share.share({ url: uri, message: CAPTION });
    return { shared: r.action !== Share.dismissedAction, note: "" };
  }
  await Clipboard.setStringAsync(CAPTION);
  if (await Sharing.isAvailableAsync()) await Sharing.shareAsync(uri, { mimeType: "image/png", dialogTitle: "Please share karo" });
  else await sendWhatsApp(CAPTION);
  return { shared: true, note: "Message copy ho gaya. WhatsApp mein photo ke neeche paste kar do." };
}
