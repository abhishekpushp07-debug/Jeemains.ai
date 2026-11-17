// Sharing the Mission card: its picture (1080 x 1350) goes out with the caption and the student's own link (see
// src/shareCard.ts for how each phone does it), and the share gate watches for the student coming back from WhatsApp.
import { AppState } from "react-native";
import { CardRef, ShareOutcome, shareCard } from "@/src/shareCard";

export type { ShareOutcome };

export const shareMission = (card: CardRef, toWhatsApp: boolean, caption: string) =>
  shareCard(card, { caption, toWhatsApp, filename: "JEELIVE-Mission.png", size: { width: 1080, height: 1350 } });

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
