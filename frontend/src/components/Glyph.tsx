import React, { memo } from "react";
import { StyleProp, ViewStyle } from "react-native";
import Svg, { Path } from "react-native-svg";
import MaterialDesignIcons from "@react-native-vector-icons/material-design-icons";
import type { IconName } from "./ui";

// Hairline outline icons (24px grid, round caps) drawn in code: calm, consistent and
// weightless in the bundle. Unknown names fall back to the material set.
const c = (x: number, y: number, r: number) => `M${x - r} ${y}a${r} ${r} 0 1 0 ${2 * r} 0a${r} ${r} 0 1 0 ${-2 * r} 0`;
const rr = (x: number, y: number, w: number, h: number, r: number) =>
  `M${x + r} ${y}h${w - 2 * r}a${r} ${r} 0 0 1 ${r} ${r}v${h - 2 * r}a${r} ${r} 0 0 1 ${-r} ${r}h${-(w - 2 * r)}a${r} ${r} 0 0 1 ${-r} ${-r}v${-(h - 2 * r)}a${r} ${r} 0 0 1 ${r} ${-r}z`;

const doc = "M14 2.5H6.5A1.5 1.5 0 0 0 5 4v16a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 20V7.5z";
const calendar = ["M8 2.5v3", "M16 2.5v3", rr(3.5, 4.5, 17, 16.5, 2.5), "M3.5 9.5h17"];
const lock = [rr(4.5, 10.5, 15, 11, 2.5), "M8 10.5V7.5a4 4 0 0 1 8 0v3"];
const star = ["M12 3l2.7 5.6 6.1.8-4.5 4.2 1.1 6.1L12 16.8l-5.4 2.9 1.1-6.1-4.5-4.2 6.1-.8z"];
const flag = ["M5 21.5V4", "M5 4.5s1.5-1 4-1 4 2 6.5 2 3.5-1 3.5-1v9s-1 1-3.5 1-4-2-6.5-2-4 1-4 1"];
const bolt = ["M13 2.5 4.5 13.5H12l-1 8 8.5-11H12z"];
const account = [c(12, 8, 4), "M4.5 20.5a7.5 7.5 0 0 1 15 0"];
const home = ["M3.5 10.2 12 3.5l8.5 6.7V19a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 19z", "M9.5 20.5v-6h5v6"];
const clipboard = [rr(8, 2.5, 8, 4, 1), "M16 4.5h2A1.5 1.5 0 0 1 19.5 6v14a1.5 1.5 0 0 1-1.5 1.5H6A1.5 1.5 0 0 1 4.5 20V6A1.5 1.5 0 0 1 6 4.5h2", "M8.5 11h7", "M8.5 15h5"];
const chart = [rr(3.5, 3.5, 17, 17, 3), "M8 16v-3", "M12 16V8", "M16 16v-5"];
const trend = ["M3.5 3.5v17h17", "m7 15 4-4 3 3 5.5-6"];
const book = ["M2.5 4.5h6a3.5 3.5 0 0 1 3.5 3.5v12.5a2.5 2.5 0 0 0-2.5-2.5h-7z", "M21.5 4.5h-6A3.5 3.5 0 0 0 12 8v12.5a2.5 2.5 0 0 1 2.5-2.5h7z"];
const bookmark = ["M18.5 21 12 17l-6.5 4V5A1.5 1.5 0 0 1 7 3.5h10A1.5 1.5 0 0 1 18.5 5z"];
const magnify = [c(11, 11, 7.5), "m20.5 20.5-4.2-4.2"];
const info = [c(12, 12, 9.5), "M12 16.5v-5", "M12 8h.01"];
const sparkles = ["M12 3.5l1.8 4.9 4.9 1.8-4.9 1.8L12 16.9l-1.8-4.9-4.9-1.8 4.9-1.8z", "M19 15.5l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"];

export const LINES: Partial<Record<IconName, string[]>> = {
  "chevron-right": ["m9 18 6-6-6-6"],
  "chevron-left": ["m15 18-6-6 6-6"],
  "chevron-down": ["m6 9 6 6 6-6"],
  "arrow-right": ["M5 12h14", "m12 5 7 7-7 7"],
  "arrow-left": ["M19 12H5", "m12 19-7-7 7-7"],
  close: ["M18 6 6 18", "m6 6 12 12"],
  check: ["M20 6 9 17l-5-5"],
  "check-circle-outline": [c(12, 12, 9.5), "m8.5 12 2.5 2.5 4.5-5"],
  play: ["M7.5 5.2v13.6a.8.8 0 0 0 1.2.7l10.6-6.8a.8.8 0 0 0 0-1.4L8.7 4.5a.8.8 0 0 0-1.2.7z"],
  pause: ["M8 5v14", "M16 5v14"],
  magnify, "magnify-plus-outline": [...magnify, "M11 8v6", "M8 11h6"], "magnify-minus-outline": [...magnify, "M8 11h6"],
  "clock-outline": [c(12, 12, 9.5), "M12 7v5l3.2 2"],
  "calendar-clock": calendar, "calendar-blank-outline": calendar, "calendar-check-outline": [...calendar, "m9 15 2 2 4-4"],
  "home-variant-outline": home, "home-variant": home,
  "atom-variant": [c(12, 12, 1), "M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5Z", "M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5Z"],
  "clipboard-text-outline": clipboard, "clipboard-text": clipboard,
  "rocket-launch-outline": [c(12, 12, 9.5), "m16.2 7.8-2.1 6.3-6.3 2.1 2.1-6.3z"], "compass-outline": [c(12, 12, 9.5), "m16.2 7.8-2.1 6.3-6.3 2.1 2.1-6.3z"],
  "lightning-bolt": bolt, "lightning-bolt-outline": bolt,
  "file-document-check-outline": [doc, "M14 2.5v5h5", "m9 15 2 2 4-4"],
  "file-document-multiple-outline": ["M15 2.5H8.5A1.5 1.5 0 0 0 7 4v13a1.5 1.5 0 0 0 1.5 1.5h9A1.5 1.5 0 0 0 19 17V6.5z", "M15 2.5v4h4", "M4 7v12.5A1.5 1.5 0 0 0 5.5 21H15"],
  "file-document-outline": [doc, "M14 2.5v5h5", "M9 13h6", "M9 17h6"],
  "book-open-page-variant-outline": book, "book-open-variant": book,
  "chart-box-outline": chart,
  podium: ["M9 20.5V8.5h6v12", "M9 12.5H3.5v8", "M15 15.5h5.5v5", "M2.5 20.5h19"],
  "chart-line-variant": trend, "chart-timeline-variant": trend, "chart-timeline-variant-shimmer": ["m3 17 6-6 4 4 8-8", "M15 7h6v6"], "trending-up": ["m3 17 6-6 4 4 8-8", "M15 7h6v6"],
  lock, "lock-outline": lock, "lock-reset": lock, "lock-clock": lock,
  "help-circle-outline": [c(12, 12, 9.5), "M9.2 9.2a2.9 2.9 0 0 1 5.6 1c0 1.9-2.8 2.6-2.8 2.6", "M12 17h.01"],
  "information-variant": info, "information-outline": info,
  "alert-circle-outline": [c(12, 12, 9.5), "M12 7.5v5", "M12 16h.01"],
  "alert-outline": ["M12 3.5 2.5 20h19z", "M12 10v4", "M12 17h.01"],
  "shield-check-outline": ["M12 21.5s7.5-3.2 7.5-9.5V5.5L12 2.5 4.5 5.5V12c0 6.3 7.5 9.5 7.5 9.5z", "m9 12 2 2 4-4"],
  speedometer: ["M4.3 18a9 9 0 1 1 15.4 0", "M12 14l3.5-4.5", c(12, 14, 1)],
  "account-remove-outline": [c(10, 7.5, 4), "M3 20.5v-1a5 5 0 0 1 5-5h4", "m16 16.5 4 4", "m20 16.5-4 4"],
  logout: ["M9.5 20.5H6A1.5 1.5 0 0 1 4.5 19V5A1.5 1.5 0 0 1 6 3.5h3.5", "m16 16.5 4.5-4.5L16 7.5", "M20.5 12H9.5"],
  login: ["M14.5 3.5H18A1.5 1.5 0 0 1 19.5 5v14a1.5 1.5 0 0 1-1.5 1.5h-3.5", "m10 16.5 4.5-4.5L10 7.5", "M14.5 12h-11"],
  "share-variant": [c(18, 5.5, 2.5), c(6, 12, 2.5), c(18, 18.5, 2.5), "m8.2 13.3 7.6 4", "m15.8 6.7-7.6 4"],
  account, "account-circle-outline": account, "account-outline": account,
  "account-group-outline": [c(9, 8, 3.5), "M2.5 20a6.5 6.5 0 0 1 13 0", "M16 4.6a3.5 3.5 0 0 1 0 6.8", "M21.5 20a6.5 6.5 0 0 0-4-6"],
  fire: ["M12 21.5a6.5 6.5 0 0 0 6.5-6.5c0-3.6-2.6-5.9-4.2-8.4-.9 2.1-2.2 3-3.3 3.3.3-2.6-.7-5.3-2.6-7.4C8.5 5.8 5.5 8.8 5.5 15a6.5 6.5 0 0 0 6.5 6.5z"],
  star, "star-outline": star, "star-plus-outline": star,
  flag, "flag-outline": flag,
  "view-grid": [rr(3.5, 3.5, 7, 7, 1.5), rr(13.5, 3.5, 7, 7, 1.5), rr(3.5, 13.5, 7, 7, 1.5), rr(13.5, 13.5, 7, 7, 1.5)],
  "bookmark-outline": bookmark, "bookmark-remove-outline": [...bookmark, "M9.5 9.5h5"],
  refresh: ["M20.5 12a8.5 8.5 0 1 1-2.5-6", "M20.5 3.5v5h-5"],
  "archive-outline": [rr(2.5, 3.5, 19, 5, 1.5), "M4.5 8.5V19A1.5 1.5 0 0 0 6 20.5h12a1.5 1.5 0 0 0 1.5-1.5V8.5", "M10 12.5h4"],
  trophy: ["M7 3.5h10v5.5a5 5 0 0 1-10 0z", "M7 5.5H4.5v1.5a3 3 0 0 0 3 3", "M17 5.5h2.5v1.5a3 3 0 0 1-3 3", "M12 14v4", "M8 20.5h8"],
  "database-search-outline": ["m12 3 9 4.5-9 4.5-9-4.5z", "m3 12 9 4.5 9-4.5", "m3 16.5 9 4.5 9-4.5"],
  "heart-outline": ["M12 20.5s-8-4.7-8-10.8A4.3 4.3 0 0 1 12 7a4.3 4.3 0 0 1 8 2.7c0 6.1-8 10.8-8 10.8z"],
  creation: sparkles,
  "phone-outline": [rr(6.5, 2.5, 11, 19, 2.5), "M11 18.5h2"],
  "eye-outline": ["M2.5 12s3.5-6.5 9.5-6.5 9.5 6.5 9.5 6.5-3.5 6.5-9.5 6.5S2.5 12 2.5 12z", c(12, 12, 3)],
  "eye-off-outline": ["M3 3l18 18", "M10.6 5.6A10 10 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-2.6 3.4", "M6.6 6.6C3.9 8.3 2.5 12 2.5 12s3.5 6.5 9.5 6.5a9.6 9.6 0 0 0 4.4-1.1", "M9.9 9.9a3 3 0 0 0 4.2 4.2"],
  cancel: [c(12, 12, 9.5), "M5.3 5.3l13.4 13.4"],
  history: ["M3.5 12a8.5 8.5 0 1 0 2.5-6", "M3.5 3.5v4h4", "M12 7.5V12l3 2"],
  "compare-horizontal": ["M8 3.5 4 7.5l4 4", "M4 7.5h16", "m16 12.5 4 4-4 4", "M20 16.5H4"],
  "school-outline": ["m12 4 10 5-10 5L2 9z", "M6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5", "M22 9v5"],
  "office-building-outline": ["M3 21h18", "M5 21V10", "M19 21V10", "M9.5 21V10", "M14.5 21V10", "m2.5 10 9.5-6.5 9.5 6.5"],
  "bullseye-arrow": [c(12, 12, 9.5), c(12, 12, 5.5), c(12, 12, 1.5)],
  "format-list-checks": ["M10 6h10.5", "M10 12h10.5", "M10 18h10.5", "m3.5 6 1.5 1.5L7.5 5", "m3.5 12 1.5 1.5 2.5-2.5", "m3.5 18 1.5 1.5 2.5-2.5"],
  plus: ["M12 5v14", "M5 12h14"],
  minus: ["M5 12h14"],
  "download-outline": ["M12 3.5v12", "m7 11 5 5 5-5", "M4 20.5h16"],
};

export const Glyph = memo(function Glyph({ name, size = 24, color, stroke = 1.6, style }: {
  name: IconName; size?: number; color?: string; stroke?: number; style?: StyleProp<ViewStyle>;
}) {
  const paths = LINES[name];
  if (!paths) return <MaterialDesignIcons name={name} size={size} color={color} style={style as any} />;
  return <Svg width={size} height={size} viewBox="0 0 24 24" style={style} pointerEvents="none">
    {paths.map((d, i) => <Path key={i} d={d} stroke={color} strokeWidth={stroke} fill="none" strokeLinecap="round" strokeLinejoin="round" />)}
  </Svg>;
});
