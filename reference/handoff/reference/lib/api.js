export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
let refreshing;
export async function api(path, options = {}, retry = true) {
  const headers =
    options.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" };
  let res;
  try {
    res = await fetch(API + path, {
      ...options,
      headers: { ...headers, ...options.headers },
      credentials: "include",
    });
  } catch {
    throw new Error(
      "Connection interrupted. Your last saved work is safe. Please try again.",
    );
  }
  if (res.status === 401 && retry && !path.startsWith("/auth/")) {
    if (!refreshing)
      refreshing = fetch(API + "/auth/refresh", {
        method: "POST",
        credentials: "include",
      }).finally(() => {
        refreshing = null;
      });
    const refresh = await refreshing;
    if (refresh.ok) return api(path, options, false);
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
export const put = (path, data) =>
  api(path, { method: "PUT", body: JSON.stringify(data) });
export async function downloadFile(path, filename) {
  let res = await fetch(API + path, { credentials: "include" });
  if (res.status === 401) {
    await post("/auth/refresh");
    res = await fetch(API + path, { credentials: "include" });
  }
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
