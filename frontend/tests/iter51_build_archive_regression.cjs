const assert = require("assert");
const fs = require("fs");
const path = require("path");
const os = require("os");
const { execFileSync, execSync } = require("child_process");
const ignore = require("ignore");

const ROOT = "/app";
const FRONTEND = "/app/frontend";

function walkRelative(baseDir) {
  const out = [];
  const stack = [""];
  while (stack.length) {
    const rel = stack.pop();
    const abs = path.join(baseDir, rel);
    const dirents = fs.readdirSync(abs, { withFileTypes: true });
    for (const d of dirents) {
      const childRel = rel ? `${rel}/${d.name}` : d.name;
      if (d.isDirectory()) {
        stack.push(childRel);
      } else if (d.isFile()) {
        out.push(childRel);
      }
    }
  }
  return out.sort();
}

function loadIgnoreRules(ignoreFilePath) {
  const text = fs.readFileSync(ignoreFilePath, "utf8");
  return ignore().add(text);
}

function includedByIgnore(baseDir, ig) {
  const all = walkRelative(baseDir);
  return all.filter((rel) => !ig.ignores(rel));
}

function stageFiles(baseDir, ig, stageDir) {
  fs.rmSync(stageDir, { recursive: true, force: true });
  // Mirror EAS vcs/local.ts: copy WORKING files, filtering before descending.
  // EAS GitClient uses --no-checkout when requireCommit is not enabled.
  fs.cpSync(baseDir, stageDir, {
    recursive: true,
    verbatimSymlinks: true,
    filter: (src) => src === baseDir || !ig.ignores(path.relative(baseDir, src)),
  });
}

function tarRoundTrip(stageDir, tarPath, extractDir) {
  fs.rmSync(tarPath, { force: true });
  fs.rmSync(extractDir, { recursive: true, force: true });
  execFileSync("tar", ["-czf", tarPath, "-C", stageDir, "."]);
  fs.mkdirSync(extractDir, { recursive: true });
  execFileSync("tar", ["-xzf", tarPath, "-C", extractDir]);
}

function listGitTrackedBytes() {
  const buf = execSync("git -C /app ls-files -z", { encoding: "buffer" });
  const entries = [];
  let start = 0;
  for (let i = 0; i < buf.length; i++) {
    if (buf[i] === 0) {
      entries.push(buf.slice(start, i));
      start = i + 1;
    }
  }
  return entries;
}

function hasInvalidUtf8(buffer) {
  try {
    const decoded = buffer.toString("utf8");
    const roundTrip = Buffer.from(decoded, "utf8");
    return !roundTrip.equals(buffer);
  } catch {
    return true;
  }
}

function walkFsUtf8Strict(baseDir) {
  const bad = [];
  const stack = [Buffer.from(baseDir)];
  while (stack.length) {
    const current = stack.pop();
    const entries = fs.readdirSync(current, { withFileTypes: true, encoding: "buffer" });
    for (const ent of entries) {
      const nameBuf = Buffer.from(ent.name);
      if (hasInvalidUtf8(nameBuf)) {
        bad.push({ dir: current.toString(), nameHex: nameBuf.toString("hex") });
      }
      const child = Buffer.concat([current, Buffer.from("/"), nameBuf]);
      if (ent.isDirectory()) {
        stack.push(child);
      }
    }
  }
  return bad;
}

function verifyNodeInvalidUtf8LstatBehavior() {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "iter51-invalid-"));
  try {
    const badBytes = Buffer.from([0x62, 0x61, 0x64, 0x2d, 0xff]); // bad-\xff
    const full = Buffer.concat([Buffer.from(tmp + "/"), badBytes]);
    fs.writeFileSync(full, "x");

    const names = fs.readdirSync(tmp, { encoding: "buffer" });
    assert.strictEqual(names.length, 1);
    const nameBuf = Buffer.from(names[0]);
    assert.ok(hasInvalidUtf8(nameBuf), "expected invalid UTF8 test fixture filename");

    const lossy = nameBuf.toString("utf8");
    assert.throws(() => fs.lstatSync(path.join(tmp, lossy)), (e) => e && e.code === "ENOENT");
    fs.lstatSync(Buffer.concat([Buffer.from(tmp + "/"), nameBuf]));
  } finally {
    fs.rmSync(tmp, { recursive: true, force: true });
  }
}

function mustContain(list, relPath) {
  assert.ok(list.includes(relPath), `expected include: ${relPath}`);
}

function mustExcludeByPattern(list, regex, message) {
  assert.ok(!list.some((x) => regex.test(x)), message);
}

function run() {
  const failures = [];
  const check = (condition, message) => {
    if (!condition) failures.push(message);
  };

  // 1) Git tracked names and filesystem strict UTF-8 scan
  const tracked = listGitTrackedBytes();
  const invalidTracked = tracked.filter(hasInvalidUtf8);
  const invalidExistingTracked = invalidTracked.filter((name) => {
    try { fs.lstatSync(Buffer.concat([Buffer.from(`${ROOT}/`), name])); return true; }
    catch (error) { if (error.code === "ENOENT") return false; throw error; }
  });
  check(invalidExistingTracked.length === 0, "existing tracked files contain invalid UTF-8 names");
  if (invalidTracked.length) {
    console.log("SNAPSHOT_WARNING: deleted invalid path remains in prior Git index; record deletion before building a fresh checkout.");
    console.log("INVALID_EXISTING_TRACKED_HEX", invalidExistingTracked.map((b) => b.toString("hex")));
  }

  // Source evidence: expo/eas-cli src/vcs/clients/git.ts makeShallowCopyAsync.
  // A residual index name does not materialize with --no-checkout. Do not claim
  // this proof for requireCommit=true or a remote checkout of an old commit.
  const eas = JSON.parse(fs.readFileSync(path.join(FRONTEND, "eas.json"), "utf8"));
  check(eas.cli?.requireCommit !== true, "this working-tree test does not cover requireCommit=true");
  check(!fs.existsSync(Buffer.concat([Buffer.from(`${FRONTEND}/`), Buffer.from("01b0d7404030b1444038", "hex")])), "corrupt file still exists on disk");

  const fsBad = walkFsUtf8Strict(FRONTEND);
  check(fsBad.length === 0, `frontend filesystem has invalid UTF-8 entries: ${JSON.stringify(fsBad.slice(0, 3))}`);

  // 2) Reproduce UTF-8/lstat behavior locally (simulation only)
  verifyNodeInvalidUtf8LstatBehavior();

  // 3) Simulate root archive input via /app/.easignore
  const rootIg = loadIgnoreRules(path.join(ROOT, ".easignore"));
  check(rootIg.ignores(".git"), "root archive must discard old Git index/objects");
  const rootIncluded = includedByIgnore(ROOT, rootIg);

  mustContain(rootIncluded, ".easignore");
  mustContain(rootIncluded, "frontend/package.json");
  mustContain(rootIncluded, "frontend/yarn.lock");
  mustContain(rootIncluded, "frontend/app.json");
  mustContain(rootIncluded, "frontend/app.config.js");
  mustContain(rootIncluded, "frontend/eas.json");
  mustContain(rootIncluded, "frontend/metro.config.js");
  mustContain(rootIncluded, "frontend/scripts/cmd-guard.js");
  mustContain(rootIncluded, "frontend/scripts/install-guard.sh");
  mustContain(rootIncluded, "frontend/scripts/sync-shims.sh");
  mustContain(rootIncluded, "frontend/scripts/cmd-guard/modes.js");
  mustContain(rootIncluded, "frontend/app/entry.tsx");
  mustContain(rootIncluded, "frontend/src/legal/content.json");
  mustContain(rootIncluded, "frontend/assets/images/tile-jee.jpg");
  mustContain(rootIncluded, "frontend/assets/website-2026-10-26/figtree-latin-400-normal.ttf");
  mustContain(rootIncluded, "frontend/assets/sfx/correct.wav");

  mustExcludeByPattern(rootIncluded, /^\.git\//, "root archive must exclude .git/");
  mustExcludeByPattern(rootIncluded, /^backend\//, "root archive must exclude backend/");
  mustExcludeByPattern(rootIncluded, /^memory\//, "root archive must exclude memory/");
  mustExcludeByPattern(rootIncluded, /^reference\//, "root archive must exclude reference/");
  mustExcludeByPattern(rootIncluded, /^frontend\/tests\//, "root archive must exclude frontend/tests/");
  mustExcludeByPattern(rootIncluded, /^frontend\/test_reports\//, "root archive must exclude frontend/test_reports/");
  mustExcludeByPattern(rootIncluded, /^frontend\/node_modules\//, "root archive must exclude frontend/node_modules/");
  mustExcludeByPattern(rootIncluded, /^frontend\/.metro-cache\//, "root archive must exclude frontend/.metro-cache/");
  mustExcludeByPattern(rootIncluded, /(^|\/)\.env($|\.)|\.env$/i, "archive must exclude env files");
  mustExcludeByPattern(rootIncluded, /\.(pem|key|jks|keystore|p8|p12|mobileprovision)$/i, "archive must exclude signing key material");
  mustExcludeByPattern(rootIncluded, /credentials\.json|token\.json/i, "archive must exclude credential-like json names");
  mustExcludeByPattern(rootIncluded, /jeelive_handoff\.zip$/i, "archive must exclude handoff zip");

  // 4) Simulate frontend-only archive via frontend/.easignore
  const feIg = loadIgnoreRules(path.join(FRONTEND, ".easignore"));
  const feIncluded = includedByIgnore(FRONTEND, feIg);

  mustContain(feIncluded, "package.json");
  mustContain(feIncluded, "yarn.lock");
  mustContain(feIncluded, "app.json");
  mustContain(feIncluded, "app.config.js");
  mustContain(feIncluded, "eas.json");
  mustContain(feIncluded, "metro.config.js");
  mustContain(feIncluded, "scripts/install-guard.sh");
  mustContain(feIncluded, "scripts/sync-shims.sh");
  mustContain(feIncluded, "scripts/cmd-guard/modes.js");
  mustContain(feIncluded, "app/entry.tsx");
  mustContain(feIncluded, "src/legal/content.json");
  mustContain(feIncluded, "assets/images/tile-jee.jpg");
  mustContain(feIncluded, "assets/website-2026-10-26/figtree-latin-400-normal.ttf");
  mustContain(feIncluded, "assets/sfx/correct.wav");
  if (fs.existsSync(path.join(FRONTEND, "babel.config.js"))) mustContain(feIncluded, "babel.config.js");

  mustExcludeByPattern(feIncluded, /^backend\//, "frontend archive must exclude backend/");
  mustExcludeByPattern(feIncluded, /^memory\//, "frontend archive must exclude memory/");
  mustExcludeByPattern(feIncluded, /^reference\//, "frontend archive must exclude reference/");
  mustExcludeByPattern(feIncluded, /^tests\//, "frontend archive must exclude tests/");
  mustExcludeByPattern(feIncluded, /^test_reports\//, "frontend archive must exclude test_reports/");
  mustExcludeByPattern(feIncluded, /^node_modules\//, "frontend archive must exclude node_modules/");
  mustExcludeByPattern(feIncluded, /^\.metro-cache\//, "frontend archive must exclude .metro-cache/");
  mustExcludeByPattern(feIncluded, /(^|\/)\.env($|\.)|\.env$/i, "frontend archive must exclude env files");
  mustExcludeByPattern(feIncluded, /\.(pem|key|jks|keystore|p8|p12|mobileprovision)$/i, "frontend archive must exclude signing key material");
  mustExcludeByPattern(feIncluded, /credentials\.json|token\.json/i, "frontend archive must exclude credential-like names");
  mustExcludeByPattern(feIncluded, /jeelive_handoff\.zip$/i, "frontend archive must exclude handoff zip");

  // 5) Tar/gzip roundtrip for both simulated archives
  const rootStage = "/tmp/iter51_root_stage";
  const rootTar = "/tmp/iter51_root_stage.tar.gz";
  const rootExtract = "/tmp/iter51_root_extract";
  stageFiles(ROOT, rootIg, rootStage);
  check(walkFsUtf8Strict(rootStage).length === 0, "root staged archive contains invalid names");
  check(!fs.existsSync(path.join(rootStage, ".git")), "root staged archive contains Git metadata");
  tarRoundTrip(rootStage, rootTar, rootExtract);
  check(fs.existsSync(path.join(rootExtract, "frontend/package.json")), "root tar extract missing frontend/package.json");

  const feStage = "/tmp/iter51_frontend_stage";
  const feTar = "/tmp/iter51_frontend_stage.tar.gz";
  const feExtract = "/tmp/iter51_frontend_extract";
  stageFiles(FRONTEND, feIg, feStage);
  check(walkFsUtf8Strict(feStage).length === 0, "frontend staged archive contains invalid names");
  tarRoundTrip(feStage, feTar, feExtract);
  check(fs.existsSync(path.join(feExtract, "package.json")), "frontend tar extract missing package.json");

  if (failures.length) {
    throw new Error(`iter51 checks failed:\n- ${failures.join("\n- ")}`);
  }

  console.log("PASS: iter51 build archive regression checks");
  console.log("NOTE: Local archive simulation only; this is NOT EAS CLI/cloud build execution.");
  console.log(`Root simulated files: ${rootIncluded.length}`);
  console.log(`Frontend simulated files: ${feIncluded.length}`);
}

try {
  run();
} catch (e) {
  console.error("FAIL: iter51 build archive regression checks");
  console.error(e && e.stack ? e.stack : e);
  process.exit(1);
}
