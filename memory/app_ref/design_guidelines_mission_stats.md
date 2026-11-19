# Mission Stats & Impact Panel: Design Guidelines

## 1. Thank-You Stats Band (Inside `MissionCard.tsx`)
**Strategy**: To prevent vertical overflow on smaller devices (288-340px) while maintaining the 4:5 ratio, we will **replace the existing "EK CHHOTI SI BAAT" eyebrow** with this new premium stats band. This acts as a certificate of honor at the very top of the card.

### Layout & Sizing (Units: `u = width/320`)
*   **Container**: 
    *   `flexDirection: 'row'`
    *   `alignItems: 'center'`
    *   `alignSelf: 'flex-start'` (Don't stretch full width)
    *   `paddingVertical: 6u`
    *   `paddingHorizontal: 12u`
    *   `borderRadius: 100u` (Pill shape)
    *   `marginBottom: 16u` (Provides breathing room before the quote starts)
*   **Visuals**:
    *   `backgroundColor`: `rgba(242, 193, 78, 0.12)` (12% of `custom_mGold` over the dark blue background)
    *   `borderWidth`: `1u`
    *   `borderColor`: `rgba(242, 193, 78, 0.35)`
*   **Content Stack (Horizontal)**:
    1.  **Icon**: `<Glyph name="star-four-points-outline" size={14u} color="#F2C14E" />` (Gold)
    2.  **Spacer**: `width: 6u`
    3.  **Text**: 
        *   Base formatting: `fontSize: 10.5u`, `color: '#DCE5FF'` (ink), `lineHeight: 14u`.
        *   Number highlight: `fontWeight: 'bold'`, `color: '#F2C14E'` (custom_mGold), `fontSize: 11.5u`.
        *   *Copy structure*: `<Text>Thank you Rahul 🙏 — aapne <Text style={boldGold}>12</Text> logon ki free education mein help ki</Text>`
    *Note: At 10.5u, a ~50 character string fits perfectly on a single line within the 320u width with margins to spare.*

---

## 2. Impact Panel (Mission Tab Screen)
**Strategy**: A premium, visually distinct panel sitting between the title and the top share button. It borrows the royal blue + gold aesthetic from the share card so the "Impact" feels highly rewarding and visually connected to the card they are sharing.

### States
**A. Helped >= 1 (Success State)**
*   **Container**: 
    *   `backgroundColor`: `#071241` (`custom_mBlueNight`)
    *   `borderRadius`: `16px`
    *   `padding`: `16px`
    *   `borderWidth`: `1px`, `borderColor`: `rgba(242, 193, 78, 0.2)`
    *   `marginBottom`: `16px`
*   **Layout**: Row-based (`flexDirection: 'row'`, `alignItems: 'center'`, `gap: 16px`)
*   **Left Column (The Metric)**:
    *   Large Count: `fontSize: 42px`, `fontWeight: '800'`, `color: '#F2C14E'`, `lineHeight: 48px`. *Requires Reanimated count-up effect (0 to N over 800ms, ease-out).*
*   **Right Column (The Message)**:
    *   Main Text: "Thank you! Aapne N logon ki free education mein help ki" (`color: '#ffffff'`, `fontSize: 14px`, `fontWeight: '600'`).
    *   Helper Text: "Jab koi dost aapke link se JEELIVE.AI kholta hai, wo yahan gina jaata hai." (`color: 'rgba(255,255,255,0.6)'`, `fontSize: 12px`, `marginTop: 4px`).
*   **Weekly Chip (Absolute Top-Right or inline if K>0)**:
    *   `backgroundColor`: `rgba(242, 193, 78, 0.15)`
    *   `borderRadius`: `6px`, `paddingHorizontal`: `8px`, `paddingVertical`: `4px`
    *   Text: "+K is hafte" (`color: '#F2C14E'`, `fontSize: 10px`, `fontWeight: 'bold'`).

**B. Helped = 0 (Empty State)**
*   **Container**: 
    *   `backgroundColor`: `rgba(11, 28, 107, 0.05)` (Very subtle blue tint on the light surface)
    *   `borderWidth`: `1px`, `borderColor`: `rgba(11, 28, 107, 0.1)`
    *   `borderStyle`: `'dashed'`
    *   `borderRadius`: `16px`, `padding`: `20px`
*   **Layout**: Center-aligned.
*   **Content**:
    *   Icon: `<Glyph name="hand-heart-outline" size={32} color="#1A36B8" />` (`custom_mBlueMid`)
    *   Text: "Aapka pehla share kisi ki free taiyari shuru karega" (`color: '#071241'`, `fontSize: 14px`, `fontWeight: '500'`, `textAlign: 'center'`, `marginTop: 12px`).

**C & D. Loading & Error States**
*   **Loading**: Standard skeleton block mirroring the Success Container's height (~100px), using Reanimated `withRepeat(withTiming)` opacity fade (0.3 to 0.7).
*   **Error**: Fail silently (render empty state B, or collapse panel entirely so it doesn't block the core share action).

---

## 3. ShareGate Screen ("Share to view results")
**Strategy**: Since the card itself will now prominently feature the golden stats band, rendering the same card on the ShareGate screen is **sufficient**. Adding redundant panels here clutters the lock-screen vibe. 

**Recommendation**: 
*   Rely on the newly added stats band inside the card.
*   *Optional*: Add a single, quiet line of text directly below the card to draw their eye to their own impact: 
    *   `<Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13, textAlign: 'center', marginTop: 12 }}>Aapka impact card par dikhega</Text>`

---

## Animation & Motion Notes
1. **Count-Up**: Use `react-native-reanimated`.
   * Create a `SharedValue` starting at 0, animated to `friends_helped` using `withTiming(count, { duration: 1200, easing: Easing.out(Easing.cubic) })`.
   * Bind to a `<TextInput>` or `ReanimatedText` wrapper, formatting via `useAnimatedProps`.
   * *Accessibility*: Wrap in an `if (!reduceMotion)` check. If reduce motion is enabled, snap immediately to the final number.
2. **Mount**: The Impact Panel should enter with a subtle `FadeInDown` (Reanimated) so it feels like a reward popping in when the Mission tab mounts.