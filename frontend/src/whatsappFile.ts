// Send a file straight into WhatsApp. Only our own Android build can do this (react-native-share's native part is not in
// Expo Go, iPhone allows no app to open WhatsApp with a file, the web has no WhatsApp intent). There WhatsApp opens with
// the file attached and the student only picks the friend. Returns false everywhere else, or if WhatsApp is missing or
// refuses, so the caller can fall back to the phone's share sheet.
import { Platform } from "react-native";
import Constants, { ExecutionEnvironment } from "expo-constants";
import type { ShareSingleOptions } from "react-native-share";

function androidShare(): typeof import("react-native-share").default | null {
  if (Platform.OS !== "android" || Constants.executionEnvironment === ExecutionEnvironment.StoreClient) return null;
  // eslint-disable-next-line @typescript-eslint/no-require-imports -- loaded only where its native part exists
  try { return require("react-native-share").default; } catch { return null; }
}

export async function sendFileToWhatsApp(o: { url: string; type: string; filename: string; message: string }): Promise<boolean> {
  const share = androidShare();
  if (!share) return false;
  const apps: [string, ShareSingleOptions["social"]][] = [["com.whatsapp", share.Social.WHATSAPP as ShareSingleOptions["social"]],
    ["com.whatsapp.w4b", share.Social.WHATSAPPBUSINESS as ShareSingleOptions["social"]]];
  for (const [pkg, social] of apps) {
    if (!(await share.isPackageInstalled(pkg).then(r => r.isInstalled).catch(() => false))) continue;
    try {
      await share.shareSingle({ social, ...o } as ShareSingleOptions);
      return true;
    } catch { return false; }
  }
  return false;
}
