# Frontend security remediation and residual risk

## Evidence and bounded change

The current React/CRA application builds successfully. Direct development packages were updated using Yarn without changing scripts, backend URL, Mongo URL or application architecture:

- ESLint9.23.0 ->9.39.5
- @eslint/js9.23.0 ->9.39.5
- PostCSS8.4.x ->8.5.30
- Resolved plugin-kit is0.4.1; Yarn refreshed compatible transitive packages.

Raw evidence:
- `test_reports/frontend_audit_current.jsonl` (before)
- `test_reports/frontend_audit_after.jsonl` (after)
- `test_reports/frontend_dependency_update.log`
- `test_reports/frontend_security_build.log`

Before:26 unique advisory IDs;299 dependency-path findings (3low,191moderate,105high).
After:25 unique advisory IDs;49 dependency-path findings (3low,25moderate,21high).
Unique after severities:1low,14moderate,10high. These are not49 distinct vulnerabilities. No critical findings were reported. **The audit is not clean.**

## Remaining blockers

Remaining packages are transitive to the deprecated CRA/react-scripts5.0.1 toolchain: webpack-dev-server, webpack-dev-middleware, PostCSS7 through resolve-url-loader, SVGO/SVGR, nth-check, selector-parser, serialize-javascript, underscore, uuid, node-forge, braces, @tootallnate/once and sprintf-js.

Most affected paths are build/test/dev-server tooling; this does **not** make them harmless. The preview runs a development server and builds parse files and process package content. An exposed dev server is not a production security boundary. Scan grouping also lists CRA under production dependencies, so `--groups dependencies` alone is not proof of browser-runtime exposure or lack of exposure.

Do not force incompatible major transitive versions simply to make an audit green. CRA and old resolver/SVGO interfaces need a controlled replacement with a maintained build tool, removal of unused old toolchain dependencies, re-audit and complete authenticated browser regression. ESLint9 is patched here but emitted an upstream unsupported-version warning; include current ESLint support in that migration.

## Remediation follow-through

1. Replace CRA/CRACO with a maintained build/dev-server tool in a dedicated bounded change; preserve REACT_APP_BACKEND_URL, /api routing, aliases, local fonts, JSX .js modules, source/PDF assets and SPA navigation.
2. Verify the existing platform startup contract before changing package scripts; retain supervisor-managed services.
3. Production must serve built static artifacts rather than a public development server. Hosting/infrastructure changes are operator responsibilities, not performed here.
4. Re-run audit, build, offline/reload, math/PDF rendering, Studio import, attempt and report flows before clearing the security release gate.

**Disposition: partially remediated; residual CRA advisories remain a release blocker.** No production-ready claim is made.

## Capacity readiness

`docs/packet1/workload.v1.json` and `docs/CAPACITY_AND_OPERATIONS.md` already contain the500k workload equations, staged campaign, SLOs and fault/restore requirements. These are planning artifacts, not measured results. The current preview lacks the independent cell/database topology, approved budgets and distributed generators required for qualification. No high-volume campaign was run on the shared preview. `capacity_qualification` remains `UNQUALIFIED`; `qualified_active_attempts` remains null. A staging-only workload generator and instrumented qualification environment are still required.
