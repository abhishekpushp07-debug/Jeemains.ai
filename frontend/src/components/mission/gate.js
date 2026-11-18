// "Share to view results": a fresh submission locks its result behind one share of the Mission card (per attempt, this browser).
const key = id => `share_gate.${id}`;
export const lockResult = id => { try { localStorage.setItem(key(id), '1'); } catch {} };
export const unlockResult = id => { try { localStorage.removeItem(key(id)); } catch {} };
export const isResultLocked = id => { try { return localStorage.getItem(key(id)) === '1'; } catch { return false; } };
