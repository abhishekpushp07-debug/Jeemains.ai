// Student Choice's chapter search (frontend/src/choice/search.ts) against the real chapter names.
// Run: node /app/tests/choice_search_check.js   (exit code 1 when a search no longer finds its chapter)
const ts = require("/app/frontend/node_modules/typescript");
const fs = require("fs");
const src = fs.readFileSync("/app/frontend/src/choice/search.ts", "utf8");
const js = ts.transpileModule(src, { compilerOptions: { module: "commonjs", target: "es2019" } }).outputText;
const m = { exports: {} };
new Function("module", "exports", "require", js)(m, m.exports, require);
const { searchIndex, findChapters } = m.exports;
// The website's JEE Main chapter-wise chapters as they were on 26 Nov 2026: [number, name, questions].
const CHAPTERS = {"Physics": [[1, "Units, Dimensions and Errors", 68], [2, "Kinematics", 66], [3, "Laws of Motion", 46], [4, "Work, Energy and Power", 42], [5, "Centre of Mass, Momentum and Collisions", 17], [6, "Rotational Motion", 60], [7, "Gravitation", 40], [8, "Mechanical Properties of Solids", 29], [9, "Fluids", 31], [10, "Surface Tension", 22], [11, "Thermal Properties of Matter", 16], [12, "Thermodynamics", 52], [13, "Kinetic Theory of Gases", 41], [14, "Oscillations", 27], [15, "Waves and Sound", 30], [16, "Electrostatics", 76], [17, "Capacitors", 30], [18, "Current Electricity", 55], [19, "Magnetic Effects of Current", 62], [20, "Magnetism and Matter", 7], [21, "Electromagnetic Induction", 34], [22, "Alternating Current", 35], [23, "Electromagnetic Waves", 41], [24, "Ray Optics and Optical Instruments", 74], [25, "Wave Optics", 49], [26, "Dual Nature of Matter and Radiation", 45], [27, "Atoms", 35], [28, "Nuclei", 30], [29, "Semiconductors and Logic Gates", 56], [30, "Experimental Skills", 34]], "Chemistry": [[1, "Mole Concept and Stoichiometry", 68], [2, "Atomic Structure", 52], [3, "Classification of Elements and Periodicity", 45], [4, "Chemical Bonding and Molecular Structure", 65], [5, "Thermodynamics and Thermochemistry", 59], [6, "Chemical Equilibrium", 31], [7, "Ionic Equilibrium", 28], [8, "Redox Reactions", 16], [9, "Solutions", 47], [10, "Electrochemistry", 56], [11, "Chemical Kinetics", 56], [12, "p-Block Elements", 54], [13, "d- and f-Block Elements", 72], [14, "Coordination Compounds", 88], [15, "Purification and Characterisation of Organic Compounds", 57], [16, "General Organic Chemistry", 103], [17, "Hydrocarbons", 58], [18, "Haloalkanes and Haloarenes", 46], [19, "Alcohols, Phenols and Ethers", 32], [20, "Aldehydes, Ketones and Carboxylic Acids", 60], [21, "Amines and Diazonium Salts", 57], [22, "Biomolecules", 56], [23, "Principles Related to Practical Chemistry", 42], [24, "Miscellaneous (beyond the current syllabus)", 2]], "Mathematics": [[1, "Sets and Relations", 38], [2, "Functions", 54], [3, "Basic Algebra (Inequalities, Modulus, Logarithms)", 13], [4, "Trigonometric Ratios, Identities and Equations", 40], [5, "Complex Numbers", 48], [6, "Quadratic Equations", 49], [7, "Permutations and Combinations", 53], [8, "Binomial Theorem", 50], [9, "Sequences and Series", 75], [10, "Straight Lines", 50], [11, "Circles", 44], [12, "Parabola", 23], [13, "Ellipse", 36], [14, "Hyperbola", 28], [15, "Limits", 29], [16, "Statistics", 29], [17, "Probability", 51], [18, "Matrices and Determinants", 86], [19, "Inverse Trigonometric Functions", 24], [20, "Continuity and Differentiability", 41], [21, "Application of Derivatives", 37], [22, "Indefinite Integration", 15], [23, "Definite Integration", 73], [24, "Area under Curves", 45], [25, "Differential Equations", 70], [26, "Vector Algebra", 67], [27, "Three-Dimensional Geometry", 82]]};
const index = searchIndex(Object.entries(CHAPTERS).map(([name, rows]) => ({ name, chapters: rows.map(([n, title, count]) => ({ id: name[0] + n, n, title, count, mcq: count, integer: 0 })) })));
let bad = 0;
const names = q => { const r = findChapters(index, q); return { close: r.close, t: r.items.map(f => f.c.title) }; };
function first(q, want, close = false) {
  const r = names(q);
  const ok = r.t[0] === want && r.close === close;
  if (!ok) bad++;
  console.log((ok ? "PASS" : "FAIL"), JSON.stringify(q).padEnd(22), "->", r.t.length, (r.close ? "(near) " : "") + r.t.slice(0, 4).join(" | "), ok ? "" : `   WANTED first: ${want}`);
}
function has(q, want, max) {
  const r = names(q);
  const ok = want.every(w => r.t.includes(w)) && (max == null || r.t.length <= max);
  if (!ok) bad++;
  console.log((ok ? "PASS" : "FAIL"), JSON.stringify(q).padEnd(22), "->", r.t.length, r.t.slice(0, 6).join(" | "), ok ? "" : `   WANTED: ${want.join(" | ")} (max ${max})`);
}
function none(q) { const r = names(q); const ok = r.t.length === 0 && !r.close; if (!ok) bad++; console.log((ok ? "PASS" : "FAIL"), JSON.stringify(q).padEnd(22), "-> nothing", ok ? "" : "   GOT: " + r.t.join(" | ")); }
// as typed
first("therm", "Thermal Properties of Matter"); has("therm", ["Thermodynamics", "Thermodynamics and Thermochemistry"], 3);
first("Electrostatics", "Electrostatics"); first("  ELECTRO  stat ", "Electrostatics");
first("laws of motion", "Laws of Motion"); first("p block", "p-Block Elements"); first("p-block", "p-Block Elements"); first("pblock", "p-Block Elements");
first("d and f", "d- and f-Block Elements"); first("d & f block", "d- and f-Block Elements");
has("organic", ["General Organic Chemistry", "Purification and Characterisation of Organic Compounds"], 2);
has("wave", ["Waves and Sound", "Wave Optics", "Electromagnetic Waves"], 3);
first("mole", "Mole Concept and Stoichiometry"); first("3 dimensional", "Three-Dimensional Geometry"); first("3 d", "Three-Dimensional Geometry"); first("combinatons", "Permutations and Combinations", true);
first("definite", "Definite Integration"); has("integration", ["Indefinite Integration", "Definite Integration"], 2);
first("optics ray", "Ray Optics and Optical Instruments");
// short names
first("goc", "General Organic Chemistry"); first("ktg", "Kinetic Theory of Gases"); first("wep", "Work, Energy and Power"); first("aod", "Application of Derivatives");
first("itf", "Inverse Trigonometric Functions"); first("ac", "Alternating Current"); first("de", "Differential Equations"); has("com", ["Centre of Mass, Momentum and Collisions", "Complex Numbers"]);
first("3d", "Three-Dimensional Geometry"); first("3D geometry", "Three-Dimensional Geometry"); first("shm", "Oscillations"); first("emi", "Electromagnetic Induction"); first("EMW", "Electromagnetic Waves");
first("nlm", "Laws of Motion"); first("pnc", "Permutations and Combinations"); first("ss", "Sequences and Series"); first("auc", "Area under Curves");
// one letter: only names with a word that starts so
has("z", [], 0); has("k", ["Kinematics", "Kinetic Theory of Gases", "Chemical Kinetics", "Aldehydes, Ketones and Carboxylic Acids"], 4);
// near spellings, only when nothing is found as typed
first("kinametics", "Kinematics", true); first("probablity", "Probability", true); first("matrix", "Matrices and Determinants", true); first("thermodinamics", "Thermodynamics", true);
first("stochiometry", "Mole Concept and Stoichiometry", true); first("gravity", "Gravitation", true); first("vectors", "Vector Algebra", true); first("intigration definite", "Definite Integration", true);
first("elctrostatics", "Electrostatics", true); first("cordination", "Coordination Compounds", true); first("hyperbolla", "Hyperbola", true);
// nothing
none("zzzz"); none("biology"); none(""); none("   "); none("!!!"); none("xyz 123");
console.log(bad ? `\n${bad} FAILED` : "\nALL PASS", "| chapters indexed:", index.length);
process.exitCode = bad ? 1 : 0;
const t0 = Date.now(); for (let i = 0; i < 2000; i++) findChapters(index, ["therm", "kinametics", "goc", "zzzzzz qqqq"][i % 4]); console.log("2000 searches:", Date.now() - t0, "ms");
