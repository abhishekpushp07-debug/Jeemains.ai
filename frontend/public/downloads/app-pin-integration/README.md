# JEELIVE PIN live integration package

PIN login and signup are now live on https://jeelive.ai. Start with NATIVE_PIN_UPDATE.md, then APP_INTEGRATION.md.

Use https://jeelive.ai/api as the canonical API. The preview-host download URL is ONLY artifact hosting, never the native API base.

This ZIP supersedes the older phone-only/pending-PIN handoff. Signup sends phone,pin,confirm_pin; login sends phone,pin; authenticated own PIN change sends phone,new_pin,confirm_pin. PINs are four-digit strings, preserving leading zeroes. No OTP, payment integration or Rapid Fire migration.

Preserve existing user IDs, sessions, saved answers, attempts/results and original solutions. Keep a valid legacy session to set the first PIN; never log out and re-register to work around an existing profile. No public PIN reset exists. Old native NEW sign-ins require the app update.

Evidence includes the live OpenAPI contracts, guest login/signup screenshots, rejected missing-PIN request422, anonymous admin request401, and canonical30PYQ/2250question catalogue read by the authorised owner. Full functional auth and two-session paper flows were tested against real backend code in isolated databases, NOT a production student or actual Expo device. No secret or private student export is included.

Exact design tokens, original licensed fonts/icons/logo, reference CSS and all existing card references are included. Home: JEE royal-blue/platinum, All India ruby/onyx, BITSAT bright amber, COMEDK teal. Other pages retain black/blood-red. Native pixel parity still requires comparison on-device.

SHA256SUMS.json lists every packaged file except itself. Keep the canonical API and Rapid Fire exception unchanged.
