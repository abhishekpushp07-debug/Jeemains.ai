import { api, uuid } from "./client";
import { storage } from "@/src/utils/storage";

/** Does not start an attempt, expose paper content, or claim full image readiness. */
export async function checkReadiness(setId: string, signal?: AbortSignal) {
  const key = `device-check.${uuid()}`;
  const marker = uuid();
  try {
    if (!await storage.setItem(key, marker) || await storage.getItem<string>(key, "") !== marker) {
      throw new Error("Device storage is unavailable. Free some space so pending answers can be kept safely.");
    }
    await api(`/sets/${encodeURIComponent(setId)}/preflight`, { method: "POST", body: { preview: false, test_response: "25" }, signal });
    return Date.now();
  } finally { await storage.removeItem(key); }
}