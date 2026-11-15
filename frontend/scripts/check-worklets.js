#!/usr/bin/env node
// Finds animation code that closes an installed phone build but works in the browser preview:
// a Reanimated worklet (it runs on the phone's UI thread) that calls an ordinary app function.
// Run from /app/frontend after touching any animation:  node scripts/check-worklets.js
const fs = require("fs");
const path = require("path");
const parser = require("@babel/parser");
const traverse = require("@babel/traverse").default;

const ROOTS = ["app", "src"];
// Callbacks the Reanimated/Worklets Babel plugin turns into worklets.
const HOOKS = new Set(["useAnimatedStyle", "useAnimatedProps", "useDerivedValue", "useAnimatedReaction", "useAnimatedScrollHandler", "useFrameCallback",
  "withTiming", "withSpring", "withDecay", "withRepeat", "runOnUI", "scheduleOnUI", "runOnUISync"]);
const GESTURE = new Set(["onBegin", "onStart", "onEnd", "onFinalize", "onUpdate", "onChange", "onTouchesDown", "onTouchesMove", "onTouchesUp", "onTouchesCancelled", "withCallback"]);
// Modules whose functions are safe to call inside a worklet.
const SAFE = /^(react-native-reanimated|react-native-worklets|react-native-gesture-handler)$/;

const files = [];
const walk = (dir) => fs.readdirSync(dir, { withFileTypes: true }).forEach((e) => {
  const p = path.join(dir, e.name);
  if (e.isDirectory()) walk(p); else if (/\.tsx?$/.test(e.name)) files.push(p);
});
ROOTS.forEach(walk);

const isFn = (n) => n && (n.type === "ArrowFunctionExpression" || n.type === "FunctionExpression" || n.type === "FunctionDeclaration");
const hasDirective = (n) => n.body?.directives?.some((d) => d.value.value === "worklet");
const problems = [];

for (const file of files) {
  const src = fs.readFileSync(file, "utf8");
  if (!/reanimated|worklets|gesture-handler|["']worklet["']/.test(src)) continue;
  const ast = parser.parse(src, { sourceType: "module", plugins: ["typescript", "jsx"] });
  const worklets = new Set();
  traverse(ast, {
    CallExpression(p) {
      const c = p.node.callee;
      const name = c.type === "Identifier" ? c.name : c.type === "MemberExpression" && c.property.type === "Identifier" && GESTURE.has(c.property.name) ? c.property.name : null;
      if (!name || !(HOOKS.has(name) || GESTURE.has(name))) return;
      p.get("arguments").forEach((a) => {
        if (isFn(a.node)) worklets.add(a);
        else if (a.isObjectExpression()) a.get("properties").forEach((prop) => { const v = prop.isObjectMethod() ? prop : prop.get("value"); if (isFn(v.node)) worklets.add(v); });
      });
    },
    Function(p) { if (hasDirective(p.node)) worklets.add(p); },
  });
  for (const w of worklets) {
    w.traverse({
      CallExpression(p) {
        const c = p.node.callee;
        const id = c.type === "Identifier" ? c : c.type === "MemberExpression" && c.object.type === "Identifier" ? c.object : null;
        if (!id) return;
        const b = p.scope.getBinding(id.name);
        if (!b || b.scope === w.scope || w.scope.hasOwnBinding(id.name) || b.path.findParent((x) => x === w)) return; // a global, or declared inside the worklet
        const node = b.path.node;
        const imported = b.path.parentPath?.isImportDeclaration() ? b.path.parentPath.node.source.value : null;
        const plain = imported ? !SAFE.test(imported)
          : c.type === "Identifier" && (isFn(node) ? !hasDirective(node) : node.type === "VariableDeclarator" && isFn(node.init) && !hasDirective(node.init));
        if (plain) problems.push(`${file}:${p.node.loc.start.line}  worklet calls "${src.slice(c.start, c.end)}"${imported ? ` (from ${imported})` : ""}`);
      },
    });
  }
}

if (problems.length) {
  console.error("Worklets calling ordinary functions (these close the installed app):\n" + problems.join("\n") + "\nUse plain values, mark the function with \"worklet\", or wrap it in runOnJS.");
  process.exit(1);
}
console.log(`Worklet check passed (${files.length} files).`);
