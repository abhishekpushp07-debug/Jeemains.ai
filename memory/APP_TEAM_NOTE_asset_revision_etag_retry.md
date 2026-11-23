# Website -> App team: asset_revision, ETag aur retry box par website ki guarantee

Likha gaya: 2026-11-23, website project ke code se (`backend/tejas/pictures.py`, `storage_move.py`, `frontend/src/components/QuestionPieces.js`).
Yeh poora note app project ki chat mein paste kar do. Detail wale routes `WEBSITE_PICTURES_REPLY_2.md` mein hain.

## 1. asset_revision (har question row par)
- Kahan milta hai: `GET /api/attempts/{id}` aur `GET /api/attempts/{id}/results` ki har question row mein, 16 hex characters.
- Guarantee: har baar padhne par same, aur dono answers mein same.
- Yeh SIRF tab badalta hai jab:
  1. us question ki koi picture (question, piece ya solution) sach mein replace ho, ya
  2. website pictures draw karne ka tareeka badle.
- Yeh NAHI badalta jab file Emergent storage se Supabase mein copy hoti hai. Copy tabhi switch hoti hai jab Supabase exactly same bytes (same SHA-256) wapas de. Isliye app ko kuch bhi dobara download nahi karna padta.
- Field na ho (purana server ya narrowed list) = apna purana cache key use karo. Null kabhi nahi bheja jaata, field bas hota nahi.
- App ke liye: cache key = `attempt/question/kind/index + asset_revision`. Revision same hai to network call ki zaroorat nahi.

## 2. ETag (one-picture route aur pack items)
- `ETag: "<32 hex>"` = jo bytes bheje gaye unke SHA-256 ke pehle 32 hex. Strong ETag hai.
- Same bytes = same ETag, chahe picture Supabase se aaye ya purane Emergent store se.
- PNG aur WebP ke ETag alag hote hain (bytes alag hain).
- `If-None-Match` match hua -> `304`, body khaali, same ETag. List, `W/"..."` aur `*` chalte hain.
- `Range: bytes=0-0` + `If-Range: <etag>` -> `206`. Purana ETag -> `200` poori nayi picture. Bahar ka range -> `416`.
- Pack items ka `etag` = one-picture route ka ETag (same picture, same format). Isse store karke baad mein 304 se check kar sakte ho.
- `Cache-Control: private, no-store` jaan-boojhkar rakha hai (private pictures). Copy app khud rakhe.
- Dhyan do: PDF se har baar draw hone wali picture pehle draw hoti hai, phir compare. 304 bytes bachata hai, server ka time nahi.

## 3. Retry box (jab picture load na ho)
- Website par picture na aaye (storage thodi der ke liye down, network, ya sirf purane store mein padi file jo abhi nahi mil rahi) to picture ki jagah ek button dikhta hai: "Picture load nahi hui. Dobara try karo".
- Button dabane par wahi picture fresh dobara maangi jaati hai. Khaali jagah ya andaza lagaya content kabhi nahi dikhaya jaata.
- Test, answers aur timer chalte rehte hain. Kuch delete nahi hota.
- Nayi files: agar Supabase set hai par down hai, to website nayi file chupke se Emergent mein NAHI daalti. Upload ka kaam rukta hai aur Supabase wapas aate hi khud chal padta hai.
- Purani Emergent files Emergent se hi padhi jaati rahengi. Copy hone ke baad bhi Emergent wali copy delete nahi hoti.
- App ko bhi yahi karna chahiye: same asset_revision ki copy pehle se hai to wahi dikhao. Copy nahi hai aur 5xx ya network error aaye to retry box dikhao. Retry ka loop khud se mat chalao, student ke tap par hi retry karo.

## 4. Kya guarantee NAHI hai
- WebP quality 90 nahi bana. Sirf lossless WebP hai, aur woh bhi PNG wapas de sakta hai (Content-Type padho).
- WebP server ki memory mein banta hai. Restart ke baad pehli request dheemi ho sakti hai.
- Storage-signed part files aur alag CDN nahi bane.
