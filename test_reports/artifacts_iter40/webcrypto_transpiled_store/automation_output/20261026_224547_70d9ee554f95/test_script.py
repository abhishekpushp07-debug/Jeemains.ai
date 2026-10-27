async def run_test(page, output_dir, page_url):
    try:
        await page.set_viewport_size({"width": 375, "height": 667})
        print("Step 1: Injecting transpiled store.web/types bundle")
        bundle = open('/tmp/iter40_storeweb_bundle.js', 'r', encoding='utf-8').read()
        await page.evaluate(bundle)

        result = await page.evaluate("""async () => {
          const checks = [];
          const store = window.__iter40Store;
          if (!store) throw new Error('Transpiled store bundle missing deviceStore export');

          const dbOpen = () => new Promise((resolve, reject) => {
            const req = indexedDB.open('jeelive-private-images-v1', 2);
            req.onsuccess = () => resolve(req.result);
            req.onerror = () => reject(req.error);
          });
          const readRecord = async (storeName, key) => {
            const db = await dbOpen();
            const out = await new Promise((resolve, reject) => {
              const tx = db.transaction(storeName, 'readonly');
              const req = tx.objectStore(storeName).get(key);
              req.onsuccess = () => resolve(req.result);
              req.onerror = () => reject(req.error);
            });
            db.close();
            return out;
          };
          const countStore = async (storeName) => {
            const db = await dbOpen();
            const count = await new Promise((resolve, reject) => {
              const tx = db.transaction(storeName, 'readonly');
              const req = tx.objectStore(storeName).count();
              req.onsuccess = () => resolve(req.result);
              req.onerror = () => reject(req.error);
            });
            db.close();
            return count;
          };

          await store.clear();
          await store.open('ownerA');
          const payload = new Uint8Array([73, 84, 69, 82, 52, 48, 95, 67, 65, 67, 72, 69]);
          await store.write('ownerA', 'f'.repeat(64), payload);
          const got = await store.read('ownerA', 'f'.repeat(64));
          checks.push({ name: 'write_reload_read_same_bytes', ok: !!got && got.length === payload.length && got.every((v, i) => v === payload[i]) });

          const account = await readRecord('meta', 'account');
          checks.push({ name: 'stored_crypto_key_nonextractable', ok: !!account?.key && account.key.extractable === false });

          const row = await readRecord('images', 'f'.repeat(64));
          const cipherTextGuess = row?.cipher ? new TextDecoder().decode(new Uint8Array(row.cipher)) : '';
          checks.push({ name: 'ciphertext_not_plaintext', ok: !cipherTextGuess.includes('ITER40_CACHE') });

          const db = await dbOpen();
          await new Promise((resolve, reject) => {
            const tx = db.transaction('images', 'readwrite');
            const s = tx.objectStore('images');
            const getReq = s.get('f'.repeat(64));
            getReq.onsuccess = () => {
              const rec = getReq.result;
              const tampered = new Uint8Array(rec.cipher);
              tampered[0] = tampered[0] ^ 0xff;
              rec.cipher = tampered.buffer;
              s.put(rec);
            };
            tx.oncomplete = () => resolve(true);
            tx.onerror = () => reject(tx.error);
          });
          db.close();

          const tamperedRead = await store.read('ownerA', 'f'.repeat(64));
          checks.push({ name: 'tampered_cipher_causes_cache_miss', ok: tamperedRead === null });

          await store.write('ownerA', 'a'.repeat(64), payload);
          await store.open('ownerB');
          const oldCount = await countStore('images');
          checks.push({ name: 'swap_account_purges_old_records', ok: oldCount === 0 });

          await store.write('ownerB', 'b'.repeat(64), payload);
          await store.clear();
          const postClearCount = await countStore('images');
          const metaCount = await countStore('meta');
          checks.push({ name: 'clear_logout_purges_images_and_meta', ok: postClearCount === 0 && metaCount === 0 });

          return { checks };
        }""")

        all_ok = all(x.get('ok') for x in result.get('checks', []))
        print(f"Step 2: Transpiled store.web test all_ok={all_ok}")
        for item in result.get('checks', []):
          print(f" - {item['name']}: {item['ok']}")

        # Get error messages using specific selectors
        error_text = await page.evaluate("""() => {
        const errorElements = Array.from(document.querySelectorAll('.error, [class*="error"], [id*="error"]'));
        return errorElements.map(el => el.textContent).join(", ");
        }""")
        if error_text:
          print(f"Found error message: {error_text}")
        else:
          print("No error messages found on the page")

        await page.screenshot(path="/app/test_reports/artifacts_iter40/webcrypto_transpiled_store/automation_output/20261026_224547_70d9ee554f95/transpiled_store_check.jpeg", type="jpeg", quality=40, full_page=False)
        print("Step 3: Captured transpiled store check screenshot")
    except Exception as e:
        print(f"Transpiled store webdriver check failed: {str(e)}")
        await page.screenshot(path="/app/test_reports/artifacts_iter40/webcrypto_transpiled_store/automation_output/20261026_224547_70d9ee554f95/transpiled_store_check_error.jpeg", type="jpeg", quality=40, full_page=False)

