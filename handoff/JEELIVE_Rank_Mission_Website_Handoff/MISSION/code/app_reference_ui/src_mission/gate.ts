// "Share to view results": every fresh test submission locks its result behind one share of the Mission card.
// The lock lives on the phone, per attempt, so leaving and reopening the result still shows the card first.
import { storage } from "@/src/utils/storage";

const key = (attemptId: string) => `share_gate.${attemptId}`;

export const lockResult = (attemptId: string) => storage.setItem(key(attemptId), true);
export const unlockResult = (attemptId: string) => storage.removeItem(key(attemptId));
export const isResultLocked = async (attemptId: string) => (await storage.getItem<boolean>(key(attemptId), false)) === true;
