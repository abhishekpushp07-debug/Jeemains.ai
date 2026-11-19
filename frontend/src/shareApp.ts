// The app's own invite: one message for the Home share card, the "share with friends" chip and Our Mission.
import { Share } from "react-native";
import { sendWhatsApp } from "@/src/rapid/social";

export const APP_LINK = "https://jeelive.ai";

export const APP_SHARE_TEXT = [
  "📚 JEELIVE.AI: 100% free JEE Main, BITSAT & COMEDK prep",
  "",
  "Built by AI after deeply analysing 4,000+ previous-year questions, so every question carries real PYQ DNA.",
  "",
  "⚡ Rapid Fire: revise fast with 20-second cards",
  "🎯 Rank: know your rank and the colleges you can get",
  "🎓 Target: aim for your dream college with the marks you need",
  "📝 Mock tests + All India Test Series: raise your chances every day",
  "",
  "The AI's goal: in every shift, 200+ marks of questions should feel familiar. Same concept, only the numbers change.",
  "",
  `100% free, forever. Join me 👉 ${APP_LINK}`,
].join("\n");

export const shareAppWhatsApp = () => sendWhatsApp(APP_SHARE_TEXT);
export const shareAppAnywhere = () => { Share.share({ message: APP_SHARE_TEXT }).catch(() => {}); };
