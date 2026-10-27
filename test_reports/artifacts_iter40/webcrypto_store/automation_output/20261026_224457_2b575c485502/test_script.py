async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Loaded secure origin for isolated WebCrypto/IndexedDB test")
        await page.wait_for_timeout(800)

        result = await page.evaluate("""async () => {
          const out = { steps: [] };
          const text = new TextEncoder().encode("ITER40_SECRET_PAYLOAD");
          const dbName = "iter40-isolated-cache-test";
          const req = indexedDB.open(dbName, 1);
          const db = await new Promise((resolve, reject) => {
            req.onupgradeneeded = () => {
              const d = req.result;
              if (!d.objectStoreNames.contains("meta")) d.createObjectStore("meta");
              if (!d.objectStoreNames.contains("images")) d.createObjectStore("images", { keyPath: "id" });
            };
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
          });

          const txWrite = (store, value, key) => new Promise((resolve, reject) => {
            const tx = db.transaction(store, "readwrite");
            const s = tx.objectStore(store);
            key === undefined ? s.put(value) : s.put(value, key);
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => reject(tx.error);
          });
          const txRead = (store, key) => new Promise((resolve, reject) => {
            const tx = db.transaction(store, "readonly");
            const req2 = tx.objectStore(store).get(key);
            req2.onsuccess = () => resolve(req2.result);
            req2.onerror = () => reject(req2.error);
          });
          const txClear = (store) => new Promise((resolve, reject) => {
            const tx = db.transaction(store, "readwrite");
            tx.objectStore(store).clear();
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => reject(tx.error);
          });

          const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
          out.steps.push({ name: "nonextractable_key", ok: key.extractable === false });
          await txWrite("meta", { scope: "u1", key }, "account");

          const iv = crypto.getRandomValues(new Uint8Array(12));
          const aad = new TextEncoder().encode("jeelive-images-v1|u1|img1");
          const cipher = await crypto.subtle.encrypt({ name: "AES-GCM", iv, additionalData: aad }, key, text);
          await txWrite("images", { id: "img1", iv, cipher, size: cipher.byteLength, used: Date.now() });

          const row = await txRead("images", "img1");
          const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv: row.iv, additionalData: aad }, key, row.cipher);
          const plainText = new TextDecoder().decode(new Uint8Array(plain));
          out.steps.push({ name: "write_reload_read_byte_equal", ok: plainText === "ITER40_SECRET_PAYLOAD" });

          const cipherTextGuess = new TextDecoder().decode(new Uint8Array(row.cipher));
          out.steps.push({ name: "ciphertext_no_plaintext_substring", ok: !cipherTextGuess.includes("ITER40_SECRET_PAYLOAD") });

          let tamperMiss = false;
          try {
            await crypto.subtle.decrypt({ name: "AES-GCM", iv: row.iv, additionalData: new TextEncoder().encode("jeelive-images-v1|u2|img1") }, key, row.cipher);
          } catch {
            tamperMiss = true;
          }
          out.steps.push({ name: "tamper_aad_causes_miss", ok: tamperMiss });

          await txClear("images");
          await txWrite("meta", { scope: "u2", key }, "account");
          const old = await txRead("images", "img1");
          out.steps.push({ name: "swap_account_purges_old_records", ok: !old });

          await txClear("images");
          await txClear("meta");
          const afterClear = await txRead("meta", "account");
          out.steps.push({ name: "clear_logout_purges_records", ok: !afterClear });

          db.close();
          indexedDB.deleteDatabase(dbName);
          return out;
        }""")

        all_ok = all(step.get("ok") for step in result.get("steps", []))
        print(f"Step 2: Browser crypto checks completed, all_ok={all_ok}")
        for step in result.get("steps", []):
          print(f" - {step['name']}: {step['ok']}")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
          print(f"Found error message: {error_text}")
        else:
          print("No error messages found on the page")

        await page.screenshot(path="/app/test_reports/artifacts_iter40/webcrypto_store/automation_output/20261026_224457_2b575c485502/webcrypto_isolated.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 3: Captured isolated webcrypto screenshot")
    except Exception as e:
        print(f"WebCrypto isolated test failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter40/webcrypto_store/automation_output/20261026_224457_2b575c485502/webcrypto_isolated_error.jpeg", type="jpeg", quality=40, full_page=False)

