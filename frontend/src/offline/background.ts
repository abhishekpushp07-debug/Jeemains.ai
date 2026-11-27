// The phone's own background run (owner, 28 Nov 2026: "App band ho tab bhi phone khud download kare", also with the
// iPhone locked): while the app is closed, the phone wakes it now and then (Android: WorkManager, every 30 minutes at
// the soonest; iPhone: when iOS chooses, mostly at night on the charger), and the app does what it does when it is
// opened: rounds played without a line go up, Rapid Fire's cards are brought up to date, then the finished papers with
// their results, solutions and pictures (./papers.ts). Both phones run it only with a network (Wi-Fi or mobile data).
//
// Rules kept exactly as on screen:
// - only the account whose session the server confirmed on this phone in the last 7 days (./identity.ts), and only
//   after the server confirms it again now; a different answer changes nothing and fetches nothing;
// - never a paper is started, nothing is answered or submitted: the same reads as an opened app;
// - nothing runs while the app is on screen (OfflineKeeper does it there);
// - the owner's switch `background` (backend/app_switches.py) set to 0 stops it on every phone at its next run.
//
// The task is defined when this file is loaded (imported through ./door.tsx by the root layout). iPhone wakes the
// whole app, so it is always defined there. On Android the run happens while the app's process is still alive (after
// it was put away); when Android has ended the process the run is skipped and the app keeps things when next opened.
// This works only in a real app build: not in Expo Go, not in the web preview (./background.web.ts does nothing).
import { AppState } from "react-native";
import * as BackgroundTask from "expo-background-task";
import * as TaskManager from "expo-task-manager";
import { api, appSwitches, askSwitches, getAssetAccount, setAssetAccount } from "@/src/api/client";
import { nameOf } from "@/src/auth";
import { flushImageDisk } from "@/src/assets/deviceCache/cache";
import { syncBank } from "./bank";
import { noteConfirmed, offlineIdentity } from "./identity";
import { keepResults, keepingHeld, stopKeeping } from "./papers";
import { sendRounds } from "./rounds";

const TASK = "jeelive.keep-offline";
const EVERY_MINUTES = 30;
// Android ends a background run after 10 minutes; the papers stop a little before (what came is kept, the rest waits).
const BUDGET_MS = 8 * 60 * 1000;

async function keepWhileClosed() {
  if (AppState.currentState === "active") return;
  const who = await offlineIdentity();
  if (!who) return;
  const timer = setTimeout(stopKeeping, BUDGET_MS);
  let expiry: { remove: () => void } | null = null;
  try { expiry = BackgroundTask.addExpirationListener(stopKeeping); } catch { expiry = null; } // the listener is the iPhone's
  try {
    const s = await api<{ user: { id: string; display_name?: string | null } | null }>("/auth/session");
    if (!s?.user || s.user.id !== who.uid) return;
    await noteConfirmed({ uid: who.uid, name: nameOf(s.user) });
    if (getAssetAccount() !== who.uid) setAssetAccount(who.uid);
    if (!appSwitches()) await askSwitches(true);
    if (Number(appSwitches()?.background ?? 1) === 0) { void scheduleKeeping(false); return; }
    await sendRounds(who.uid).catch(() => {});
    await syncBank(who.uid).catch(() => {}); // the cards' trouble never keeps the papers from coming
    if (!keepingHeld()) await keepResults(who.uid);
  } finally {
    clearTimeout(timer); expiry?.remove();
    await flushImageDisk(); // the list of the pictures that came is written before the phone puts the app to sleep
  }
}

TaskManager.defineTask(TASK, async () => {
  try { await keepWhileClosed(); return BackgroundTask.BackgroundTaskResult.Success; }
  catch { return BackgroundTask.BackgroundTaskResult.Failed; } // trouble of any kind waits for the next run
});

/** On after every confirmed session, off after signing out or a session the server ended. Never throws. */
export async function scheduleKeeping(on: boolean): Promise<void> {
  try {
    const registered = await TaskManager.isTaskRegisteredAsync(TASK);
    if (on && !registered && Number(appSwitches()?.background ?? 1) !== 0) {
      if ((await BackgroundTask.getStatusAsync()) === BackgroundTask.BackgroundTaskStatus.Available) await BackgroundTask.registerTaskAsync(TASK, { minimumInterval: EVERY_MINUTES });
    } else if (!on && registered) await BackgroundTask.unregisterTaskAsync(TASK);
  } catch { /* Expo Go, or a phone that does not allow it: the app keeps things while it is open, as before */ }
}
