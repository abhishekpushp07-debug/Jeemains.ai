import { Platform } from "react-native";
import { AssetValue } from "./PrivateAssetQueue";
import { imageGrant } from "./assetGrants";
import { readSavedImage, saveImage } from "./deviceCache/cache";
import { SavedImage } from "./deviceCache/types";

export type ImageResponse = { status: number; headers: Headers; bytes: Uint8Array };
export type ImageTransport = (path: string, signal: AbortSignal, extra?: Record<string, string>) => Promise<ImageResponse>;
const stopped = () => Object.assign(new Error("Image loading stopped."), { name: "AbortError" });
export function unchangedImage(saved: SavedImage, response: ImageResponse) {
  if (response.status === 304) return true;
  if (response.status !== 206) return false;
  const etag = response.headers.get("etag"), modified = response.headers.get("last-modified");
  const length = Number(response.headers.get("content-range")?.split("/").pop());
  if (saved.etag && !saved.etag.startsWith("W/") && etag === saved.etag) return true;
  return !saved.etag && !!saved.modified && modified === saved.modified && length === saved.bytes.length;
}
export async function originalImageValue(image: SavedImage, signal: AbortSignal): Promise<AssetValue> {
  if (signal.aborted) throw stopped();
  const blob = new Blob([image.bytes.slice().buffer], { type: image.mime });
  if (Platform.OS === "web" && typeof URL.createObjectURL === "function") {
    const uri = URL.createObjectURL(blob); return { uri, bytes: blob.size, dispose: () => URL.revokeObjectURL(uri) };
  }
  const uri = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    const abort = () => { reader.abort(); reject(stopped()); };
    signal.addEventListener("abort", abort, { once: true });
    reader.onloadend = () => { signal.removeEventListener("abort", abort); if (typeof reader.result === "string") resolve(reader.result); else reject(new Error("Image decoding failed.")); };
    reader.onerror = reject; reader.readAsDataURL(blob);
  });
  return { uri, bytes: uri.length * 2 };
}
export async function loadOriginalImage(path: string, signal: AbortSignal, transport: ImageTransport): Promise<AssetValue> {
  const grant = imageGrant(path);
  if (!grant) throw stopped();
  const ensureCurrent = () => { if (signal.aborted || imageGrant(path) !== grant) throw stopped(); };
  const saved = await readSavedImage(grant.contentKey);
  ensureCurrent();
  if (saved && grant.validated) return originalImageValue(saved, signal);
  let response: ImageResponse | null = null;
  if (saved && (saved.etag || saved.modified)) {
    const headers: Record<string, string> = { Range: "bytes=0-0" };
    if (saved.etag) headers["If-None-Match"] = saved.etag;
    if (saved.etag && !saved.etag.startsWith("W/")) headers["If-Range"] = saved.etag;
    else if (saved.modified) headers["If-Range"] = saved.modified;
    response = await transport(path, signal, headers); ensureCurrent();
    if (unchangedImage(saved, response)) { grant.validated = true; return originalImageValue(saved, signal); }
  }
  if (!response || response.status !== 200) response = await transport(path, signal);
  ensureCurrent();
  const mime = (response.headers.get("content-type") || "").split(";")[0];
  if (!mime.startsWith("image/") || response.status !== 200 || !response.bytes.length) throw new Error("The original image could not be read. Please retry.");
  const image: SavedImage = { bytes: response.bytes, mime, etag: response.headers.get("etag") || "", modified: response.headers.get("last-modified") || "" };
  grant.validated = true;
  void saveImage(grant.contentKey, image); // Encryption/persistence never delays first paint.
  return originalImageValue(image, signal);
}