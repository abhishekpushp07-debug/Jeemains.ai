# Question pictures CDN se — setup (2026-11-18)

## Kya bana hai
- Paper khulte hi website `GET /api/attempts/{id}/assets/links` se paper ki pictures ke **public links** leti hai. Ek din mein ek paper ke sab students ko **same links** milte hain.
- Har link mein 12 pictures hain, usi format mein jo `/assets/pack` deta tha. Links signed hain, sirf us student ko milte hain jiska paper khul chuka hai, aur 1–2 din mein expire ho jaate hain. Inmein answers ya solutions kabhi nahi hote.
- Server har link ke saath `Cache-Control: public, max-age=86400, s-maxage=86400, immutable` aur `Access-Control-Allow-Origin: *` bhejta hai. Isliye koi bhi CDN ek part server se sirf ek baar lega aur baaki sab students ko khud dega.
- Link fail ho to website khud purane private `/assets/pack` par jaati hai, phir ek-ek picture par. Paper kabhi atakta nahi.
- RedOS app ke liye contract: `docs/APP_INTEGRATION.md` section 15.

## Abhi (CDN ke bina) kya hota hai
- Jab tak `MEDIA_CDN_URL` khaali hai, links jeelive.ai par hi hain (`/api/media/pack/...`). jeelive.ai ka current edge (Emergent ka Cloudflare) static files bhi cache nahi karta (`cf-cache-status` header nahi aata), isliye pictures abhi bhi server se jaati hain.
- Fir bhi server par kaam kam hua hai: ek part ek baar banta hai, phir memory se jaata hai. Login, database aur 16-slot read line ki zaroorat nahi padti. Pictures ki apni 32-slot line hai. Ek saath 20 requests ek naye part par aayein to bhi woh sirf ek baar banta hai.

## CDN lagane ke 3 steps (koi API key nahi chahiye)
1. Koi bhi **pull CDN** lo: BunnyCDN Pull Zone, AWS CloudFront, ya apne Cloudflare account par ek alag hostname (jaise `cdn.jeelive.ai`).
   - **Origin**: `https://jeelive.ai`
   - **Host header**: `jeelive.ai` bhejo (BunnyCDN: "Forward Host Header" OFF; CloudFront: origin domain `jeelive.ai`).
   - **Caching**: "origin ke Cache-Control headers maano" (BunnyCDN: Cache Expiration "Respect origin"; CloudFront: policy `CachingOptimized` ya "Use origin cache headers").
   - Sirf `/api/media/*` path is CDN se jaaye (CloudFront behaviour path pattern `/api/media/*`; BunnyCDN Edge Rule baaki path block kare). Login, answers aur results kabhi CDN se nahi jaane chahiye.
   - Cookies aur query strings forward mat karo. `Access-Control-Allow-Origin` header ko pass hone do.
2. CDN ka address (jaise `https://jeelive-pics.b-cdn.net` ya `https://cdn.jeelive.ai`, end mein `/` nahi) backend setting `MEDIA_CDN_URL` mein daalo. Phir re-publish karo.
3. Check karo: `curl -I <CDN address>/api/media/probe.bin` do baar chalao. Doosri baar HIT aana chahiye (BunnyCDN `cdn-cache: HIT`, CloudFront `x-cache: Hit from cloudfront`, Cloudflare `cf-cache-status: HIT`). `x-media-cdn` header se pata chalta hai ki server ko CDN address mila ya nahi. Phir paper kholo: network mein `.../api/media/pack/...bin` links CDN host par dikhne chahiye.

## Kharcha (andaza)
- Ek JEE paper ~7.4 MB pictures. 1 lakh students = ~740 GB, 2 lakh = ~1.5 TB ek paper par. Yeh CDN ka bandwidth bill hai; server par sirf har part ki pehli copy jaati hai (har CDN location se ek baar).

## Tests
- `backend/tests/media_cdn_iso198.py`: isolated DB, 29/29 pass (same links for all students, public headers, bytes = private pack, tampered/expired link 404 no-store, broken picture never cached, 20 cold requests build once, CDN host in links).
- Purane pack tests: `get_ready_iso188.py` 47/47, `get_ready_iso189.py` 15/15.
