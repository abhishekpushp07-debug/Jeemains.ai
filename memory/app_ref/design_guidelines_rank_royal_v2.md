# JEELIVE.AI - Royal Rank Tab Theme Spec (v2)

## 1. Global Page Background
- **Base Fill**: `#04070D` (Deep Void)
- **Glow Blobs** (Absolute positioned SVGs with radial gradients / blur):
  - **Blob 1 (Top Right)**: `rgba(11, 37, 105, 0.35)` (Sapphire), 200px radius, blur 80px.
  - **Blob 2 (Bottom Left)**: `rgba(60, 20, 85, 0.25)` (Amethyst), 250px radius, blur 100px.

## 2. Segmented Switch (JEE Main / BITSAT / COMEDK)
- **Container**: `rgba(255, 255, 255, 0.05)`, Border: `rgba(255, 255, 255, 0.1)`, Radius: `pill` (24px).
- **Unselected Text**: `#8E9BB0` (Figtree 14px, 500).
- **Selected Pill**: 
  - Gradient: `linear-gradient(90deg, #102A4A 0%, #06405C 100%)`
  - Border: `rgba(74, 213, 255, 0.3)` 1px.
- **Selected Text**: `#4AD5FF` (Cyan, Figtree 14px, 600) + subtle text shadow `rgba(74, 213, 255, 0.5)`.

## 3. The 5 Tool Tiles (2x2 Grid + 1 Full Width)
Every tile has an unselected and selected state. The selected state gets a brighter gradient, gold frame, and inner glow.

### Tile 1: Rank Predictor (Ruby / Garnet)
- **Unselected Gradient**: `linear-gradient(135deg, #1E0A10 0%, #0D0306 100%)`
- **Selected Gradient**: `linear-gradient(135deg, #3A0D1A 0%, #17040A 100%)`
- **Icon/Ink Accent**: `#E63956`

### Tile 2: Percentile Se Rank (Sapphire)
- **Unselected Gradient**: `linear-gradient(135deg, #0A1326 0%, #050812 100%)`
- **Selected Gradient**: `linear-gradient(135deg, #11254D 0%, #080D21 100%)`
- **Icon/Ink Accent**: `#4A8BFF`

### Tile 3: Target Marks (Emerald)
- **Unselected Gradient**: `linear-gradient(135deg, #061A16 0%, #020A08 100%)`
- **Selected Gradient**: `linear-gradient(135deg, #0A2E26 0%, #041410 100%)`
- **Icon/Ink Accent**: `#20C997`

### Tile 4: College Predictor (Amethyst)
- **Unselected Gradient**: `linear-gradient(135deg, #150B21 0%, #0A0412 100%)`
- **Selected Gradient**: `linear-gradient(135deg, #2A1442 0%, #12071C 100%)`
- **Icon/Ink Accent**: `#B266FF`

### Tile 5: College Compare (Topaz / Bronze)
- **Unselected Gradient**: `linear-gradient(135deg, #1C1107 0%, #0C0602 100%)`
- **Selected Gradient**: `linear-gradient(135deg, #331D0A 0%, #170A03 100%)`
- **Icon/Ink Accent**: `#F5A623`

### Tile Shared Styles
- **Border Unselected**: `rgba(255, 255, 255, 0.08)` 1px.
- **Border Selected**: `linear-gradient(135deg, #F3E5AB 0%, #D4AF37 50%, #8A6D1C 100%)` 1px.
- **Inner Glow (Selected)**: inset shadow `rgba(212, 175, 55, 0.2)` blur 12px.
- **Title Text**: `#FFFFFF` (Figtree 14px).

## 4. Input Panel & Summary Strip (Glass Panels)
Distinct from the jewel tiles, these act as functional control surfaces.
- **Input Panel Background**: `rgba(16, 22, 36, 0.45)` (Cool Glass) + backdrop blur 20px.
- **Input Panel Border**: Top edge highlight `rgba(255, 255, 255, 0.15)`.
- **Text Input Fill**: `rgba(4, 7, 13, 0.6)`, Border `rgba(255,255,255,0.1)`. Text: `#FFFFFF`.
- **Chips (General/OBC, Tough/Easy)**:
  - Unselected: `rgba(255, 255, 255, 0.05)`, Text `#8E9BB0`.
  - Selected: `rgba(212, 175, 55, 0.15)`, Border `#D4AF37` 1px, Text `#F3E5AB`.
- **Primary Button**:
  - Gradient: `linear-gradient(90deg, #C59B27 0%, #D4AF37 50%, #E8C96B 100%)`
  - Text: `#04070D` (Dark Navy for max contrast, Figtree 16px, 600).
- **Summary Strip Background**: `linear-gradient(90deg, rgba(28, 36, 56, 0.8) 0%, rgba(16, 22, 36, 0.8) 100%)`.

## 5. Hero Rank Card (The Crown Jewel)
- **Background Gradient**: `linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(12, 20, 40, 0.8) 50%, rgba(4, 7, 13, 0.95) 100%)`
- **Border**: `#D4AF37` 1px solid.
- **Inner Glow**: Top-left radial sheen `rgba(243, 229, 171, 0.15)`.
- **Big Number Text**: `#F3E5AB` (Georgia/Serif, 42px).
- **Label Text**: `#B0C4DE` (Light Steel Blue, Figtree 12px).

## 6. List Panel & Rows (College Detail)
- **List Panel Background**: `rgba(8, 12, 22, 0.7)` (Deep Neutral Navy, lets rows pop).
- **Row Backgrounds** (Alternating/Tiered):
  - **Rank 1 (Gold)**: `linear-gradient(90deg, rgba(212, 175, 55, 0.12) 0%, rgba(212, 175, 55, 0.0) 100%)`
  - **Rank 2 (Silver)**: `linear-gradient(90deg, rgba(192, 192, 192, 0.1) 0%, rgba(192, 192, 192, 0.0) 100%)`
  - **Rank 3 (Bronze)**: `linear-gradient(90deg, rgba(205, 127, 50, 0.1) 0%, rgba(205, 127, 50, 0.0) 100%)`
  - **Standard Rows**: `transparent`.
- **Row Separator**: `rgba(255, 255, 255, 0.04)` 1px bottom border.
- **College Name Text**: `#FFFFFF` (Figtree 16px, 500).
- **Trend Text**: Green `#20C997`, Red `#E63956`.
- **Medals**: Rendered as SVG circles. Gold: `#D4AF37`, Silver: `#C0C0C0`, Bronze: `#CD7F32`.

## 7. College Detail Bottom Sheet
- **Background**: `#080C16` (Opaque for readability).
- **Drag Handle**: `rgba(255, 255, 255, 0.2)`.
- **Table Headers**: `rgba(255, 255, 255, 0.03)` fill.
- **Table Borders**: `rgba(255, 255, 255, 0.08)`.