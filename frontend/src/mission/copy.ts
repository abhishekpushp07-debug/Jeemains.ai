// Everything the Mission tab and its share card say, in short Hinglish, in one place.
import { IconName } from "@/src/components/ui";

export const MAKER = "Abhishek Pushp";
export const LINK = "jeelive.ai";

/** The card's four promises: title + a one-line version. */
export const SEGMENTS: { icon: IconName; title: string; short: string }[] = [
  { icon: "dna", title: "PYQ DNA", short: "4,000+ PYQs se bana har sawaal" },
  { icon: "bullseye-arrow", title: "Target 200+", short: "har session 200+ marks ka target" },
  { icon: "lightning-bolt", title: "Rapid Fire", short: "revision ka competitive game" },
  { icon: "school-outline", title: "Rank + College", short: "dream college kitni door?" },
];

/** The full story under the card, one segment each. */
export const POINTS: { icon: IconName; title: string; body: string }[] = [
  { icon: "heart-outline", title: "100% free, hamesha", body: "Koi fees nahi, koi paywall nahi. Abhishek Pushp ne ise AI ke saath, apne kharche par, bahut mehnat se banaya hai." },
  { icon: "dna", title: "Har sawaal ka DNA = PYQ", body: "Saare sawaal deeply PYQ-based hain. Har sawaal ka DNA 4,000+ PYQs analyse karke bana hai, isliye ye kisi bhi institute se better hain." },
  { icon: "bullseye-arrow", title: "Target: 200+ marks", body: "Hamara target hai ki har session mein 200+ marks ke sawaal bilkul isi Mock aur All India Test Series jaise aayein." },
  { icon: "lightning-bolt", title: "Rapid Fire", body: "Aapke revision ke liye ek highly competitive game. 15 second mein ek concept, doston se seedha muqabla." },
  { icon: "school-outline", title: "Rank + College predictor", body: "Aapke mann ki shaanti ke liye, taaki pata rahe ki aapka dream college bas kitni door hai." },
  { icon: "rocket-launch-outline", title: "Aage aur bhi aayega", body: "Koshish hai ki aane wale waqt mein features aur badhein. Aapka ek share is mission ko aage badhata hai." },
];

/** Goes with the card picture (or alone, where a picture cannot be sent). `link` is the student's own link. */
export const caption = (link: string) => [
  "🙏 Please share karo aur free education ko support karo!",
  "",
  "JEELIVE.AI: 100% free JEE Main, BITSAT & COMEDK prep. Abhishek Pushp ne ise AI ke saath, apne kharche par banaya hai.",
  "",
  "🧬 Har sawaal ka DNA 4,000+ PYQs analyse karke bana",
  "🎯 Target: har session 200+ marks ke sawaal isi Mock aur All India Test Series se",
  "⚡ Rapid Fire: revision ka competitive game",
  "🎓 Rank + College predictor: dream college kitni door?",
  "",
  `Abhi kholo 👉 ${link}`,
].join("\n");
