import { useEffect, useSyncExternalStore } from "react";
import { AppState, Linking, Share } from "react-native";
import { useSegments } from "expo-router";
import { RF_BASE, rf } from "@/src/api/client";
import { useAuth } from "@/src/auth";
import { useCached } from "@/src/useCached";
import type { Pick } from "./scope";

// Rapid Fire social data shared by the arena screens: the inbox (presence, challenge banner, notices), friends and gangs.
export type PlayerCard = { pid: string; name: string; avatar?: string | null; frame?: string | null; entry?: string | null; level: number; online: boolean; seen_ts?: number | null };
export type GangTag = { id: string; name: string; emblem: string };
export type GangRow = GangTag & { members: number; online: number; leader: boolean };
export type ChallengeNote = { id: string; subject: string; chapter?: string | null; label: string; revenge: boolean; expires_in: number; joined: number; seats: number; single: boolean; gang: GangTag | null;
  vs?: { a: GangTag; b: GangTag } | null; team?: "a" | "b" | null; from: PlayerCard };
export type CupNote = { id: string; label: string; size: number; joined: number; expires_in: number; from: PlayerCard };
export type Notice = { id: string; kind: "friend_added" | "gang_added"; ts: number; gang?: GangTag | null; from: PlayerCard };
export type Inbox = { me: PlayerCard; room: string | null; cup: string | null; cups: CupNote[]; challenges: ChallengeNote[]; notices: Notice[] };
export type Friend = PlayerCard & { follows_you: boolean };

export const shortSubject = (s?: string) => (s === "Mathematics" ? "Maths" : s || "");
export const clock = (s: number) => `${Math.floor(s / 60)}:${String(Math.max(0, s % 60)).padStart(2, "0")}`;
export const ordinal = (n: number) => `${n}${["th", "st", "nd", "rd"][n % 10 > 3 || Math.floor(n / 10) === 1 ? 0 : n % 10]}`;
export const roomLink = (cid: string) => `${RF_BASE}/c/${cid}`;

// Friend Code: the only way to become friends. Shown in two groups of four so it is easy to read out.
export const cleanCode = (text: string) => text.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
export const prettyCode = (code?: string | null) => (code ? `${code.slice(0, 4)} ${code.slice(4)}` : "");
export const useFriendCode = (uid?: string) => useCached<{ code: string }>(uid ? `u.${uid}.rfcode` : null, () => rf("/friends/code", uid!));
export const shareFriendCode = (code: string) =>
  sendWhatsApp(`Add me on JEECIRCLE.AI Rapid Fire and let’s see who is faster!\nMy Friend Code: ${prettyCode(code)}\nIn the app: Rapid Fire → Gang → Enter a friend’s code.`);

export async function sendWhatsApp(text: string) {
  try { await Linking.openURL("whatsapp://send?text=" + encodeURIComponent(text)); }
  catch {
    try { await Linking.openURL("https://wa.me/?text=" + encodeURIComponent(text)); }
    catch { Share.share({ message: text }).catch(() => {}); }
  }
}

let inbox: Inbox | null = null, fetchedAt = 0;
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((f) => f());
const subscribe = (f: () => void) => { listeners.add(f); return () => { listeners.delete(f); }; };
const read = () => inbox;

export async function refreshInbox(uid: string) {
  try { inbox = await rf<Inbox>("/inbox", uid); fetchedAt = Date.now(); emit(); } catch { /* the next poll retries */ }
}
export const useInbox = () => useSyncExternalStore(subscribe, read, read);
/** Seconds since the inbox was read, to keep countdowns moving between polls. */
export const inboxAge = () => (Date.now() - fetchedAt) / 1000;

/** Keeps the player online and the challenge banner fresh while the app is open. Rests during a test. */
export function InboxPoller() {
  const { user } = useAuth();
  const inTest = (useSegments()[0] as string) === "attempt";
  const uid = user?.id;
  useEffect(() => {
    if (!uid) { inbox = null; emit(); return; }
    if (inTest) return;
    refreshInbox(uid);
    const iv = setInterval(() => { if (AppState.currentState === "active") refreshInbox(uid); }, 6000);
    return () => clearInterval(iv);
  }, [uid, inTest]);
  return null;
}

// Which arena tab is showing. Any screen can switch it (coins "+" opens the Store, a quest nudge opens Rewards).
export type ArenaTab = "arena" | "trophy" | "gang" | "store";
let arenaTab: ArenaTab = "arena", arenaPart = "";
const tabListeners = new Set<() => void>();
const readTab = () => arenaTab;
export function setArenaTab(tab: ArenaTab, part = "") { arenaTab = tab; arenaPart = part; tabListeners.forEach((f) => f()); }
export const useArenaTab = () => useSyncExternalStore((f) => { tabListeners.add(f); return () => { tabListeners.delete(f); }; }, readTab, readTab);
/** The section a tab should open on (Trophy: ranks / rewards / matches, Store: avatar / entry / ...). Read once. */
export const takeArenaPart = () => { const part = arenaPart; arenaPart = ""; return part; };

// Routes of the arena's inner screens.
export const go = {
  player: (pid: string) => ({ pathname: "/rapid/player/[pid]", params: { pid } }) as any,
  gang: (gid: string) => ({ pathname: "/rapid/gang/[gid]", params: { gid } }) as any,
  duel: (params: Record<string, string>) => ({ pathname: "/rapid/duel", params }) as any,
  challenge: (params: { pid?: string; gang?: string } = {}) => ({ pathname: "/rapid/challenge", params }) as any,
  /** A Match Room, or straight into the match when it has already started. */
  room: (room: { id: string; duel_id?: string | null }) => (room.duel_id ? go.duel({ did: room.duel_id }) : ({ pathname: "/rapid/room/[cid]", params: { cid: room.id } }) as any),
  cups: () => "/rapid/cup" as any,
  cup: (cid: string) => ({ pathname: "/rapid/cup/[cid]", params: { cid } }) as any,
  watch: (did: string) => ({ pathname: "/rapid/watch/[did]", params: { did } }) as any,
};
/** Send a challenge to one friend, several friends, a whole gang, a rival gang (Gang War), or everyone from a finished match (rematch, Badla). */
export const sendChallenge = (uid: string, body: { pids?: string[]; gang_id?: string; rival_gang_id?: string; rematch_of?: string; picks?: Pick[] }) =>
  rf<any>("/challenges", uid, { method: "POST", body });

// Matches your friends and gang mates are playing right now, to watch live.
export type LiveMatch = { id: string; label: string; cup: boolean; started: boolean; total: number; teams: string[] | null; players: { name: string; avatar?: string | null; frame?: string | null; score: number; answered: number }[] };
export const useLiveMatches = (uid?: string) => useCached<{ items: LiveMatch[] }>(uid ? `u.${uid}.rflive` : null, () => rf("/duels/live", uid!), false);
/** "5 min ago", "3 h ago", "2 d ago" for a time given in seconds. */
export const ago = (ts: number) => {
  const min = Math.max(1, Math.round((Date.now() / 1000 - ts) / 60));
  return min < 60 ? `${min} min ago` : min < 1440 ? `${Math.round(min / 60)} h ago` : `${Math.round(min / 1440)} d ago`;
};
export const day = (iso?: string) => (iso ? new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "");
export const seenText = (p: { online?: boolean; seen_ts?: number | null }) => (p.online ? "Online" : p.seen_ts ? `Active ${ago(p.seen_ts)}` : "Offline");

// Friend activity: what the players you added did in the arena over the last 7 days.
export type FeedItem = { id: string; kind: "win" | "run" | "gem" | "level" | "badge"; data: Record<string, any>; ts: number; from: PlayerCard };
export const useFeed = (uid?: string) => useCached<{ items: FeedItem[] }>(uid ? `u.${uid}.rffeed` : null, () => rf("/feed", uid!), false);

export const useFriends = (uid?: string) => useCached<{ items: Friend[] }>(uid ? `u.${uid}.rffriends` : null, () => rf("/friends", uid!), false);
export const useGangs = (uid?: string) => useCached<{ items: GangRow[] }>(uid ? `u.${uid}.rfgangs` : null, () => rf("/gangs", uid!), false);
