const fs = require("fs");
const ts = require("/app/frontend/node_modules/typescript");

const typesPath = "/app/frontend/src/assets/deviceCache/types.ts";
const storePath = "/app/frontend/src/assets/deviceCache/store.web.ts";
const outPath = "/tmp/iter40_storeweb_bundle.js";

const transpile = (file) => ts.transpileModule(fs.readFileSync(file, "utf8"), {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    esModuleInterop: true,
  },
  fileName: file,
}).outputText;

const typesJs = transpile(typesPath);
const storeJs = transpile(storePath);

const bundle = [
  "(function(){",
  "  const modules = { './types': { exports: {} }, './store': { exports: {} } };",
  "  (function(require,module,exports){",
  typesJs,
  "  })(null, modules['./types'], modules['./types'].exports);",
  "  (function(require,module,exports){",
  storeJs,
  "  })(",
  "    (id) => {",
  "      if (id === './types') return modules['./types'].exports;",
  "      throw new Error('Unsupported require in bundle: ' + id);",
  "    },",
  "    modules['./store'],",
  "    modules['./store'].exports",
  "  );",
  "  window.__iter40Store = modules['./store'].exports.deviceStore;",
  "})();",
  "",
].join("\n");

fs.writeFileSync(outPath, bundle, "utf8");
console.log(outPath);
