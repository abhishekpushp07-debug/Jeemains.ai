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

/** Returns a note to show under the buttons ("" when nothing needs saying). */
export async function shareMission(card: React.RefObject<React.ComponentRef<typeof View> | null>, toWhatsApp: boolean): Promise<string> {
  if (Platform.OS === "web") {
    if (toWhatsApp) { await sendWhatsApp(CAPTION); return ""; }
    try { await Share.share({ message: CAPTION }); return ""; }
    catch { await Clipboard.setStringAsync(CAPTION); return "Message copy ho gaya. Kahin bhi paste karke bhej do."; } // browsers without a share sheet
  }
  const uri = await captureRef(card, { format: "png", quality: 1, result: "tmpfile", width: 1080, height: 1350 });
  if (toWhatsApp && await sendFileToWhatsApp({ url: uri, type: "image/png", filename: "JEELIVE-Mission.png", message: CAPTION })) return "";
  if (Platform.OS === "ios") { await Share.share({ url: uri, message: CAPTION }); return ""; }
  await Clipboard.setStringAsync(CAPTION);
  if (await Sharing.isAvailableAsync()) await Sharing.shareAsync(uri, { mimeType: "image/png", dialogTitle: "Please share karo" });
  else await sendWhatsApp(CAPTION);
  return "Message copy ho gaya. WhatsApp mein photo ke neeche paste kar do.";
}
