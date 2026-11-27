import { Dimensions, Platform } from "react-native";
import { arena } from "@/src/theme";

/** The browser arena: the web build served by our server under /api/arena, Rapid Fire only. */
export const ARENA_BASE = "/api/arena";
export const ARENA = Platform.OS === "web" && typeof window !== "undefined" && (window.location.pathname === ARENA_BASE || window.location.pathname.startsWith(ARENA_BASE + "/"));
/** Where "home" is: the arena lobby in the browser arena, the Home tab in the app. */
export const HOME_ROUTE = (ARENA ? "/(tabs)/rapid" : "/(tabs)") as "/(tabs)";
// Rapid Fire screens plus sign-in, PIN help, policies and the account page (to sign out on a shared computer).
// "offline": a Solo Sprint from the cards this browser keeps, when the server cannot be heard (src/offline).
const ARENA_ROUTES = ["rapid", "entry", "forgot-pin", "privacy", "delete-account", "account", "change-pin", "offline"];
export const arenaAllows = (segments: string[]) => !segments.length || ARENA_ROUTES.includes(segments[0]) || (segments[0] === "(tabs)" && segments[1] === "rapid");

// On a laptop the arena stays a phone-wide column with the blood-red stage on both sides.
const COLUMN = 480;
if (ARENA) {
  document.title = "Rapid Fire · JEELIVE.AI";
  const style = document.createElement("style");
  // A transform on <body> keeps every fixed layer (sheets, celebrations) inside the column.
  style.textContent = `html{background:${arena.bg} radial-gradient(ellipse at 50% 0,${arena.bgTop},${arena.bg} 55%,${arena.bgDeep});min-height:100%}
body{max-width:${COLUMN}px;width:100%;margin:0 auto!important;transform:translateZ(0);box-shadow:0 0 80px ${arena.vignette}}`;
  document.head.appendChild(style);
  // Screens size themselves from the window: give them the column's width, not the laptop's.
  const D = Dimensions as any, get = D.get.bind(D), add = D.addEventListener.bind(D), remove = D.removeEventListener.bind(D);
  // The same window gives the same object back, so screens do not redraw for nothing.
  let source: any = null, clamped: any = null;
  const clamp = (w: any) => {
    if (!w || w.width <= COLUMN) return w;
    if (source !== w) { source = w; clamped = { ...w, width: COLUMN }; }
    return clamped;
  };
  const wrapped = new WeakMap<Function, Function>();
  D.get = (key: string) => (key === "window" ? clamp(get(key)) : get(key));
  D.addEventListener = (type: string, handler: Function) => {
    const wrap = (dims: any) => handler({ ...dims, window: clamp(dims.window) });
    wrapped.set(handler, wrap);
    return add(type, wrap);
  };
  D.removeEventListener = (type: string, handler: Function) => remove(type, wrapped.get(handler) || handler);
}
