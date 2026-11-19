# JEELIVE.AI - Rank Tab Royal Theme Blueprint

## 1. Core Palette & Token Overrides

This blueprint replaces the monotonous graphite/red theme with an elegant, premium "Royal Leaderboard" visual language based on deep midnight-navy, antique gold frames, and cyan/teal glass glows. 

**No new image assets or fonts are required.** We use existing standard React Native components (`LinearGradient`, `Svg`, standard views) to achieve the effects.

### A. Theme Overrides (`rankColors`)
Override the light palette values when in the Rank tab context:

```typescript
const rankColors = {
  surface: '#05080F',             // Deep midnight navy base
  onSurface: '#F0F4F8',           // Crisp white-blue for max readability
  surfaceSecondary: '#0B1221',    // Elevated navy glass for cards
  onSurfaceSecondary: '#E2E8F0',  // Secondary text
  surfaceTertiary: '#131C31',     // Deepest nesting (inputs, chips)
  onSurfaceTertiary: '#CBD5E1',
  muted: '#64748B',               // Dimmed text, subtle hairlines
  
  brandPrimary: '#00E5FF',        // Cyan glow for active states/tabs
  brandText: '#E8C37B',           // Elegant Gold for primary titles
  
  // Tag Semantics (Safe / Likely / Borderline)
  success: '#00E5FF',             // Safe: Cyan/Teal (fits the leaderboard vibe better than standard green)
  successSoft: '#00E5FF1A',
  warning: '#E8C37B',             // Likely: Gold
  warningSoft: '#E8C37B1A',
  error: '#F43F5E',               // Borderline: Rose/Crimson
  errorSoft: '#F43F5E1A',
  info: '#3B82F6',
  infoSoft: '#3B82F61A',
};
```

### B. Custom Rank Tokens (`custom_rank*`)
Replace the existing `custom_rank*` keys with these values:

```typescript
const custom_rank = {
  // Background Gradients
  BgFrom: '#05080F',
  BgMid: '#0A101D',
  BgTo: '#03050A',
  BgGlow: '#00E5FF15',            // Subtle cyan radial glow behind hero elements
  
  // Gold & Metals
  Gold: '#E8C37B',
  GoldMuted: '#A67C00',
  GoldSoft: '#E8C37B26',
  Silver: '#C0C0C0',
  Bronze: '#CD7F32',
  
  // Card & Panel Styling
  Card: '#0B1221',
  CardRaised: '#131C31',
  CardLine: '#1E293B',            // Default thin border for unselected cards
  CardLineStrong: '#00E5FF80',    // Cyan hairline for selected/active rows
  
  // Typography & Accents
  Eyebrow: '#00E5FF',             // Cyan for tracked caps (— JEELIVE.AI · RANK)
  Dim: '#475569',
  SoftText: '#94A3B8',
  
  // Effects
  Glow: '#00E5FF',                // Active cyan glow
  Sheen: '#FFFFFF1A',             // Glass reflection
  Sparkle: '#E8C37B',             // Gold twinkling stars
  Track: '#0F172A',               // Progress bar track
};
```

---

## 2. Component Specifications

### A. Royal Gold Frame (Hero `MetalCard` & Selected `ToolGrid` Tile)
To achieve the "Royal Gold Frame" without images, use a gradient border technique.
*   **Wrapper:** `<LinearGradient>` with `padding: 1.5` (or `1` for smaller tiles).
*   **Gradient Stops (Outer):** `['#F9E596', '#A67C00', '#E8C37B', '#7A5C00']` (Angle: 45deg).
*   **Inner Panel:** A standard `<View>` with `backgroundColor: custom_rank.Card` and `borderRadius` slightly smaller than the wrapper to fit perfectly.
*   **Inner Sheen:** Add a subtle radial gradient or a top-edge linear gradient `['#FFFFFF15', 'transparent']` inside the inner panel to give it a glass volume.

### B. Medal Coins (List Ranks 1, 2, 3 & 4+)
Rendered purely via SVG circles and text. Size: `28px` to `32px`.
*   **Rank 1 (Gold):** 
    *   Outer Circle: `stroke="url(#goldGrad)" strokeWidth="2"`
    *   Inner Circle: `fill="#2A1F00"` (Dark gold ink)
    *   Text: `fill="#E8C37B"` (Serif, bold)
    *   Glow: `shadowColor: '#E8C37B', shadowOpacity: 0.6, shadowRadius: 4`
*   **Rank 2 (Silver):**
    *   Outer Circle: `stroke="#E2E8F0" strokeWidth="2"`
    *   Inner Circle: `fill="#0F172A"`
    *   Text: `fill="#F8FAFC"`
*   **Rank 3 (Bronze):**
    *   Outer Circle: `stroke="#CD7F32" strokeWidth="2"`
    *   Inner Circle: `fill="#2A1600"`
    *   Text: `fill="#E8A87C"`
*   **Rank 4+ (Navy-Gold):**
    *   Outer Circle: `stroke="#1E293B" strokeWidth="1"`
    *   Inner Circle: `fill="#0B1221"`
    *   Text: `fill="#94A3B8"` (Standard sans-serif)

### C. Ornamental Divider (`—◆—`)
Replace the current red hairline in `Strip` with an elegant ornamental divider.
*   **Layout:** `flexDirection: 'row', alignItems: 'center', justifyContent: 'center'`
*   **Lines:** `<View style={{ height: 1, flex: 1, backgroundColor: '#1E293B' }} />`
*   **Center Ornament:** `<Text style={{ color: '#E8C37B', fontSize: 10, marginHorizontal: 8 }}>◆</Text>`
*   **Title:** Tracked caps (`letterSpacing: 2`), Serif, Color: `#E8C37B`.

### D. Segmented Switch (Cyan Glow)
*   **Container:** `backgroundColor: '#05080F', borderWidth: 1, borderColor: '#1E293B', borderRadius: 99`
*   **Selected Tab:** 
    *   `backgroundColor: '#00E5FF15'`
    *   `borderWidth: 1, borderColor: '#00E5FF'`
    *   `shadowColor: '#00E5FF', shadowOffset: {width: 0, height: 0}, shadowOpacity: 0.8, shadowRadius: 8`
*   **Selected Text:** `color: '#00E5FF', fontWeight: '600'`
*   **Unselected Text:** `color: '#64748B'`

### E. List Row Styling (`SeatList`, `Comedk`, `Bitsat`)
*   **Background:** `backgroundColor: '#0B1221'` (Navy Glass)
*   **Border:** `borderBottomWidth: 1, borderBottomColor: '#1E293B'`
*   **User's Own Row (Highlight):** `backgroundColor: '#00E5FF0A', borderWidth: 1, borderColor: '#00E5FF80'`
*   **Text:** College Name (`#F0F4F8`, 500 weight), Branch (`#94A3B8`, 400 weight).
*   **Numbers (Closing Rank):** Soft cyan `#00E5FF` or crisp white `#F0F4F8` using a tabular-nums font variant if available.

### F. Tag Colors (Chance Pills)
*   **Safe:** `color: '#00E5FF', backgroundColor: '#00E5FF1A', borderColor: '#00E5FF40', borderWidth: 1`
*   **Likely:** `color: '#E8C37B', backgroundColor: '#E8C37B1A', borderColor: '#E8C37B40', borderWidth: 1`
*   **Borderline:** `color: '#F43F5E', backgroundColor: '#F43F5E1A', borderColor: '#F43F5E40', borderWidth: 1`
*   **Exam/Kind/Level Chips:** Use muted navy glass (`backgroundColor: '#131C31', color: '#CBD5E1', borderWidth: 1, borderColor: '#1E293B'`).

### G. Screen Background & Title Treatment
*   **Background:** `<LinearGradient colors={['#05080F', '#0A101D', '#03050A']} style={StyleSheet.absoluteFill} />`
*   **Glow:** Position an absolute `<LinearGradient>` or SVG radial gradient at the top center (behind the hero card) with `colors={['#00E5FF15', 'transparent']}` spanning 300px.
*   **Title ("Rank & college predictor"):** 
    *   Font: `SERIF` constant.
    *   Color: `#E8C37B` (Gold).
    *   Shadow: `textShadowColor: '#E8C37B40', textShadowOffset: {width: 0, height: 2}, textShadowRadius: 4`.
*   **Eyebrow ("— JEELIVE.AI · RANK"):** Tracked caps (`letterSpacing: 2`), Color: `#00E5FF`, FontSize: 10.

### H. Sparkle Stars
*   **Color:** `#E8C37B` (Gold).
*   **Animation:** Keep the existing twinkling opacity animation, but ensure the SVG fill is strictly gold, removing any previous "sparkle silver" or red tints.

---

## 3. Elegance Constraints (Where NOT to use Gold)
To prevent the UI from looking gaudy or overwhelming:
1.  **DO NOT** use gold for body text, college names, or standard data rows. Keep those crisp white/blue (`#F0F4F8`) or muted navy-grey (`#94A3B8`).
2.  **DO NOT** use gold for the segmented switch or standard buttons. Use Cyan (`#00E5FF`) for interactive/selected states to maintain the "game leaderboard" tech-glass contrast.
3.  **DO NOT** fill large backgrounds with gold. Gold is strictly for **borders (1-1.5px)**, **serif titles**, **medals**, and **ornamental dividers**.
4.  **DO NOT** use heavy drop shadows. Use glowing drop shadows (`shadowColor: '#00E5FF'`) only on active/selected elements. Unselected elements should remain flat against the dark navy background to emphasize depth.