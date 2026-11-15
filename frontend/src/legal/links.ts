import { Linking } from "react-native";
import { BACKEND } from "@/src/api/client";
import content from "./content.json";

export const privacyContact = content.supportEmail;
export const legalUrl = (page: "privacy" | "delete-account") => {
  if (!BACKEND) throw new Error("The public policy address is not configured.");
  const url = new URL(`/api/legal/${page}`, BACKEND);
  if (url.protocol !== "https:") throw new Error("A secure policy address is required.");
  return url.href;
};
export async function openLegal(page: "privacy" | "delete-account") { await Linking.openURL(legalUrl(page)); }
export async function contactPrivacy() {
  await Linking.openURL(`mailto:${privacyContact}?subject=${encodeURIComponent("JEELIVE.AI privacy support")}`);
}