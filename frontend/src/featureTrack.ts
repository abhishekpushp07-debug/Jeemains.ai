// Analytics (src/jlTracker.ts): feature_entry_viewed each time a student comes into one of the app's features.
// Moving about inside a feature (Misfire's list, then one paper's page) is one entry, not several.
import { useEffect } from "react";
import { usePathname } from "expo-router";
import { track } from "@/src/jlTracker";

const FEATURES: [RegExp, string][] = [
  [/^\/misfire(\/|$)/, "misfire"], [/^\/choice(\/|$)/, "choice"], [/^\/matched(\/|$)/, "matched"],
  [/^\/rapid\/vault(\/|$)/, "vault"], [/^\/rapid\/gang(\/|$)/, "gangs"], [/^\/rapid\/squads(\/|$)/, "squads"], [/^\/rapid\/cup(\/|$)/, "cups"],
  [/^\/mission(\/|$)/, "mission"], [/^\/performance(\/|$)/, "performance"], [/^\/offline(\/|$)/, "offline"],
];

let current = ""; // the feature the student is in now ("" = none); one entry each time it changes to a feature

/** The student is now in `feature` ("" = in none of them): counted once per entry. Also called for features that are
 * a part of a screen (the Rapid Fire Store, Trophy and Gang tabs, the Rank tab's Dream tool). */
export function enterFeature(feature: string) {
  if (feature && feature !== current) track("feature_entry_viewed", { feature });
  current = feature;
}

/** Mounted once in the root layout: the features that are screens of their own. On the Rapid Fire tab itself the tab
 * says which of its parts is open (app/(tabs)/rapid.tsx), so a gang tab, then a gang's page, is one entry. */
export function FeatureTracker(): null {
  const path = usePathname();
  useEffect(() => {
    if (path === "/rapid") return;
    enterFeature(FEATURES.find(([re]) => re.test(path || ""))?.[1] || "");
  }, [path]);
  return null;
}
