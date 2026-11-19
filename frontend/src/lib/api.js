export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
let refreshing;
let refreshVersion = 0;
let studioActive = 0;
const studioWaiters = [];
async function fetchStudioRead(url, options) {
  if (studioActive >= 3) await new Promise(resolve => studioWaiters.push(resolve));
  else studioActive += 1;
  try {
    return await fetch(url, options);
  } finally {
    if (studioWaiters.length) studioWaiters.shift()();
    else studioActive -= 1;
  }
}
export function refreshSession() {
  if (!refreshing) refreshing = fetch(API + '/auth/refresh', {method:'POST', credentials:'include'}).then(response => { if(response.ok)refreshVersion+=1;return response; }).finally(() => { refreshing = null; });
  return refreshing;
}
export async function fetchWithSession(path, options = {}, retry = true) {
  const request = path.startsWith('/studio/') && (!options.method || options.method === 'GET') ? fetchStudioRead : fetch;
  const initialRefresh = refreshVersion;
  let response = await request(API + path, {...options, credentials:'include'});
  if (response.status === 401 && retry && !path.startsWith('/auth/')) {
    const refreshed = initialRefresh === refreshVersion ? await refreshSession() : {ok:true};
    if (refreshed.ok) response = await request(API + path, {...options, credentials:'include'});
  }
  if (response.status === 401 && !path.startsWith('/auth/')) window.dispatchEvent(new Event('tejas-session-lost'));
  return response;
}
export async function api(path, options = {}, retry = true) {
  const headers =
    options.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" };
  let res;
  try {
    res = await fetchWithSession(path, {
      ...options,
      headers: { ...headers, ...options.headers },
    }, retry);
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error(
      "Connection interrupted. Your last saved work is safe. Please try again.",
    );
  }
  if (!res.ok) {
    let data;
    try {
      data = await res.json();
    } catch {}
    if (res.status === 413 && options.body instanceof FormData)
      throw new Error(
        "The upload exceeds the allowed size. Keep PDFs under 50 MB; split larger files and retry.",
      );
    const d = data?.error?.message || data?.detail;
    const err = new Error(
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d.map((x) => x.msg).join(". ")
          : "This request could not finish. Please try again.",
    );
    err.status = res.status;
    const hint = res.headers.get('Retry-After');
    const seconds = Number(hint);
    err.retryAfterMs = hint ? (Number.isFinite(seconds) ? seconds * 1000 : Math.max(0, Date.parse(hint) - Date.now())) : 0;
    throw err;
  }
  const body = await res.json();
  return body &&
    Object.prototype.hasOwnProperty.call(body, "data") &&
    body.meta?.api_version
    ? body.data
    : body;
}
export const post = (path, data = {}) =>
  api(path, { method: "POST", body: JSON.stringify(data) });
// For requests that are safe to repeat (sign-in, start with a start key): a busy server is retried quietly a few times.
export async function postWhenFree(path, data = {}, tries = 4) {
  for (let i = 1; ; i++) {
    try {
      return await post(path, data);
    } catch (e) {
      if (e.status !== 503 || i >= tries) throw e;
      await new Promise(resolve => setTimeout(resolve, Math.min(8000, (e.retryAfterMs || 2000) * i) + Math.random() * 1000));
    }
  }
}
export const put = (path, data) =>
  api(path, { method: "PUT", body: JSON.stringify(data) });
export const del = path => api(path, { method: 'DELETE' });
export const patch = (path, data) =>
  api(path, { method: "PATCH", body: JSON.stringify(data) });
export async function downloadFile(path, filename) {
  const res = await fetchWithSession(path);
  if (!res.ok)
    throw new Error(
      "The file is unavailable. Retry generation, or sign in again.",
    );
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
}
