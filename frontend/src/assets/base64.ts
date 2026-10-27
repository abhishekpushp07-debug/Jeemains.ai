const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
/** No Blob/FileReader roundtrip on Android. Yield between bounded chunks. */
export async function imageBase64(bytes: Uint8Array, signal: AbortSignal) {
  const parts: string[] = [];
  const chunk = 48 * 1024; // divisible by 3: padding only at the end
  for (let start = 0; start < bytes.length; start += chunk) {
    if (signal.aborted) throw Object.assign(new Error("Image loading stopped."), { name: "AbortError" });
    const end = Math.min(bytes.length, start + chunk);
    let part = "";
    for (let i = start; i < end; i += 3) {
      const a = bytes[i], b = bytes[i + 1] || 0, c = bytes[i + 2] || 0;
      part += alphabet[a >> 2] + alphabet[((a & 3) << 4) | (b >> 4)] + (i + 1 < end ? alphabet[((b & 15) << 2) | (c >> 6)] : "=") + (i + 2 < end ? alphabet[c & 63] : "=");
    }
    parts.push(part);
    if (end < bytes.length) await new Promise<void>(resolve => setTimeout(resolve, 0));
  }
  return parts.join("");
}