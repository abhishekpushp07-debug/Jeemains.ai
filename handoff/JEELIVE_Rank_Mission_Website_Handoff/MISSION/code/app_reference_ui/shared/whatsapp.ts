// Opens WhatsApp with a ready message (the app keeps this helper in a shared module; copied here on its own).
import { Linking, Platform, Share } from "react-native";

export async function sendWhatsApp(text: string) {
  // api.whatsapp.com directly: the wa.me redirect breaks some emoji in the message.
  const web = "https://api.whatsapp.com/send?text=" + encodeURIComponent(text);
  if (Platform.OS === "web") { await Linking.openURL(web).catch(() => {}); return; } // a computer may have no WhatsApp app
  try { await Linking.openURL("whatsapp://send?text=" + encodeURIComponent(text)); }
  catch {
    try { await Linking.openURL(web); }
    catch { Share.share({ message: text }).catch(() => {}); }
  }
}
