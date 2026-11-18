import { Platform } from "react-native";

export const usesNativeTabs = Platform.OS === "ios" && parseInt(String(Platform.Version), 10) >= 26;

export const EXAMS = [
  { slug: "jee-main", name: "JEE Main", tone: "jee" },
  { slug: "bitsat", name: "BITSAT", tone: "bitsat" },
  { slug: "comedk", name: "COMEDK", tone: "comedk" },
] as const;

export const istDate = (d: string) => new Date(d + "T12:00:00+05:30").toLocaleDateString("en-IN", { day: "numeric", month: "short", timeZone: "Asia/Kolkata" });
export const unixDate = (t?: number | null) =>
  t ? new Date(t * 1000).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit", timeZone: "Asia/Kolkata" }) : "—";
export const fmtClock = (s: number) => {
  const h = Math.floor(s / 3600),
    m = Math.floor((s % 3600) / 60),
    sec = s % 60;
  return (h ? h + ":" + String(m).padStart(2, "0") : String(m)) + ":" + String(sec).padStart(2, "0");
};
/** Time spent, in words a student reads at once: "2 min 53 sec", "1 hr 05 min". */
export const fmtSpent = (s: number) => {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = Math.round(s % 60);
  return h ? `${h} hr ${String(m).padStart(2, "0")} min` : m ? `${m} min ${String(sec).padStart(2, "0")} sec` : `${sec} sec`;
};
