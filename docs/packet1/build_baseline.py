"""Rebuild versioned Packet 1 inventories; never mark source coverage complete.

Run after the API is available. Reads specification PDFs, lockfiles and public
OpenAPI only. No application database import, secret values or source URLs.
"""
import ast
import csv
import hashlib
import importlib.metadata
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import fitz
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/packet1'
sys.path.insert(0, str(ROOT / 'backend'))
from tejas.capacity import calculate
from tejas.command_contracts import CommandIntent, CommandReceipt, ExactMarks, SourceAnchor, CandidateQuestion


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


# Manually separated obligations. These are a REVIEWED SUBSET, not all177pages.
# Test references are requirements-to-evidence targets, not evidence of success.
CLAUSES = [
    ('IDENTITY-01', 5, [1, 43], 10, 'Active attempts, not idle users, define the 500000 target', 'capacity.calculate', 'capacity_arithmetic'),
    ('IDENTITY-02', 1, [1, 26], 3, 'Phone-only student entry is an explicit user override, not verified ownership', 'auth/phone', 'phone_only'),
    ('SOURCE-01', 5, [11], 5, 'Locked original bytes and approved truth are never edited in place', 'source-vault', 'locked_truth_denial'),
    ('SOURCE-02', 5, [11, 16], 5, 'Corrections create reviewed successor versions', 'content-version-repository', 'successor_version'),
    ('SOURCE-03', 5, [11, 26], 6, 'Active attempts retain pinned question/key/rule/release versions', 'attempt-repository', 'pinned_versions'),
    ('SOURCE-04', 5, [26, 42], 5, 'Candidate packages exclude keys, hidden answers and source maps', 'CandidateQuestion', 'candidate_projection'),
    ('SOURCE-05', 5, [14, 25], 3, 'Source/candidate/key/solution classes have separated workload authority', 'data-ownership-map', 'artifact_identity_isolation'),
    ('SOURCE-06', 3, [1, 2, 3], 5, 'Each question preserves exact matched solution and source provenance', 'SourceAnchor', 'source_pairing'),
    ('SOURCE-07', 5, [11, 16], 5, 'Academic approval and source rights are independent publication gates', 'publication-policy', 'publication_rights'),
    ('SECURITY-01', 5, [13, 14], 3, 'Privileged staff authenticate with MFA before a secondary action gate', 'staff-identity-provider', 'staff_mfa'),
    ('SECURITY-02', 5, [13, 38], 3, 'Single-use grants bind actor/session/tenant/target/version/action/diff/reason/nonce', 'protected-command-repository', 'grant_binding'),
    ('SECURITY-03', 5, [13], 3, 'Failed verifier/secrets/policy/grant services deny protected actions', 'grant-policy', 'fail_closed_dependencies'),
    ('SECURITY-04', 5, [13, 38], 1, 'Credentials and verifiers never appear in evidence/log payloads', 'safe-evidence', 'evidence_redaction'),
    ('API-01', 5, [28], 1, 'Versioned executable OpenAPI and local JSON Schemas identify every operation', 'operation_catalogue', 'catalogue_coverage'),
    ('API-02', 5, [28], 1, 'Every operation declares ownership, roles, lane, idempotency, body budgets and errors', 'operation_catalogue', 'catalogue_metadata'),
    ('API-03', 5, [29], 6, 'Same operation key and intent return the original durable outcome', 'CommandIntent', 'A01'),
    ('API-04', 5, [29], 6, 'Changed intent under the same scoped key conflicts', 'CommandIntent', 'command_scope'),
    ('API-05', 5, [28, 38], 5, 'Protected edits enforce exact parent preconditions and review invalidation', 'editorial-repository', 'A03'),
    ('API-06', 5, [29, 40], 4, 'Durable async acceptance exposes typed receipt, status, Location and Retry-After', 'job-repository', 'async_receipt'),
    ('LIVE-01', 5, [44, 45], 2, 'Assign and persist one home cell before attempt admission', 'admission-repository', 'home_cell'),
    ('LIVE-02', 5, [44, 45], 2, 'Never reroute active writers as ordinary load balancing', 'routing-policy', 'writer_isolation'),
    ('LIVE-03', 5, [7, 30, 31, 50], 6, 'Admission consumption, attempt creation, receipt and capacity charge are atomic', 'admission-repository', 'reservation_atomicity'),
    ('LIVE-04', 5, [7, 30, 31, 50], 6, 'Acquire the serializing lock before sampling authoritative cutoff time', 'command-repository', 'cutoff_lock_wait'),
    ('LIVE-05', 5, [30, 31, 50], 6, 'Draft persistence is distinct from grading-eligible explicit commitment', 'command-repository', 'committed_a_draft_b'),
    ('LIVE-06', 5, [31, 50], 6, 'Writer generations fence every authoritative mutation', 'command-repository', 'stale_writer'),
    ('LIVE-07', 5, [31, 50], 6, 'Seal admitted watermark, classify/drain eligible work before final grading', 'terminal-repository', 'seal_drain'),
    ('LIVE-08', 5, [2, 44, 52], 2, 'Global catalogue, analytics and optional reports cannot block admitted commits', 'data-ownership-map', 'control_outage'),
    ('WORKER-01', 5, [40, 44, 52], 4, 'Durable queued work drains autonomously without browser polling', 'job-repository', 'A05'),
    ('WORKER-02', 5, [10, 40, 50], 4, 'Destination writes participate in the current generation/lease authority', 'job-repository', 'A06'),
    ('WORKER-03', 5, [21, 40, 52], 4, 'Untrusted parse resource limits apply before expensive processing', 'upload-sandbox', 'S01'),
    ('GRADE-01', 2, [13, 18], 6, 'Exact scoring uses only final committed responses and pinned rules', 'ExactMarks', 'exact_marks'),
    ('ANALYTICS-00', 4, [1], 8, 'Deliver all60 analyses, with unavailable states for missing evidence', 'analysis-registry', 'all_60'),
    ('ANALYTICS-61', 5, [2, 64, 68], 8, 'Analytical materializations never query the live writer for each page', 'analytics-snapshot-repository', 'no_hot_scans'),
    ('REPORT-01', 4, [19, 20, 21, 22, 23], 9, 'Screen and complete PDF share one immutable grade/version and release policy', 'report-snapshot', 'snapshot_pdf_parity'),
    ('SCALE-01', 5, [3, 46, 56], 1, 'Versioned workload includes independent commit/draft/lease/telemetry streams', 'capacity.calculate', 'capacity_arithmetic'),
    ('SCALE-02', 5, [47, 56, 59], 10, 'Start and submission waves overlay the surviving baseline', 'capacity.calculate', 'capacity_overlays'),
    ('SCALE-03', 5, [43, 48], 10, 'Machine counts require measured unit capacity and approved quota evidence', 'capacity-evidence', 'no_unqualified_claim'),
    ('SCALE-04', 5, [52, 63], 10, 'Budget and overload controls protect admitted sessions ahead of optional work', 'admission-policy', 'optional_shedding'),
    ('EVIDENCE-01', 5, [57], 10, 'Actor, browser and connection evidence are independent tracks', 'run-manifest', 'three_tracks'),
    ('EVIDENCE-02', 5, [58], 10, 'All six exact active-soak stages pass before final qualification', 'capacity.calculate', 'capacity_stages'),
    ('EVIDENCE-03', 5, [55, 61], 10, 'Evaluate latency and error gates overall and in predeclared critical windows', 'slo-manifest', 'critical_windows'),
    ('EVIDENCE-04', 5, [58, 68], 10, 'Under-generated or generator-saturated runs fail', 'run-manifest', 'offered_load'),
    ('EVIDENCE-05', 5, [60, 62], 10, 'Covered crash/AZ loss preserves acknowledged commits; regional loss is disclosed', 'restore-evidence', 'receipt_reconciliation'),
    ('EVIDENCE-06', 5, [61], 10, 'Metrics use bounded labels without learner or attempt identities', 'metric-contract', 'metric_cardinality'),
    ('EVIDENCE-07', 5, [66, 68], 10, 'Release evidence binds tested artifacts, signed digests, SBOM and compatible migrations', 'release-evidence', 'same_artifact'),
]


def source_inventory():
    manifest = json.loads((ROOT / 'docs/source_guides/manifest.json').read_text())
    pages, blocks, sources = [], [], []
    for item in sorted(manifest, key=lambda x: x['name']):
        path = ROOT / 'docs/source_guides' / item['name']
        if digest(path.read_bytes()) != item['sha256']:
            raise ValueError('Source hash drift: stop for source review')
        number = int(item['name'][:2])
        with fitz.open(path) as pdf:
            if len(pdf) != item['pages']:
                raise ValueError('Source page count drift')
            sources.append({k: item[k] for k in ('name', 'pages', 'sha256')})
            for page in pdf:
                pid = f'PDF{number:02d}-P{page.number + 1:03d}'
                page_blocks = []
                for index, block in enumerate(page.get_text('blocks')):
                    if block[6] != 0 or not block[4].strip():
                        continue
                    bid = f'{pid}-B{index:03d}'
                    page_blocks.append(bid)
                    text = block[4]
                    blocks.append({'id': bid, 'source': number, 'page_1based': page.number + 1,
                        'bbox_points': list(block[:4]), 'content_sha256': digest(text.encode()),
                        'review_status': 'UNREVIEWED_SOURCE_BLOCK',
                        'mandatory_keyword_candidate': bool(re.search(r'\b(must|required|never|shall|acceptance|fail|gate)\b', text, re.I)),
                        'warning': 'Block may contain zero, one or several atomic clauses; keywords are not coverage'})
                pages.append({'id': pid, 'source': number, 'page_1based': page.number + 1,
                    'text_sha256': digest(page.get_text().encode()), 'block_ids': page_blocks,
                    'review_status': 'UNREVIEWED_FOR_COMPLETE_ATOMIZATION'})
    return sources, pages, blocks


def requirements():
    records = []
    for cid, source, pages, packet, text, boundary, test in CLAUSES:
        records.append({'id': cid, 'source': f'PDF-{source:02d}', 'pages_1based': pages,
            'obligation': text, 'scope': 'reviewed_subset_not_exhaustive', 'repair_packet': packet,
            'owner_role': 'operator' if packet == 10 else 'application_lead', 'contract_boundary': boundary,
            'depends_on_packets': list(range(1, packet)), 'acceptance_target': test,
            'evidence': [], 'implementation_status': 'UNVERIFIED'})
    for row in csv.DictReader((ROOT / 'docs/audit/analytics_60_matrix.csv').open()):
        records.append({'id': 'ANALYSIS-' + row['id'], 'source': 'PDF-04', 'pages_1based': [int(row['pdf_page'])],
            'obligation': row['name'], 'scope': 'feature_obligation_needs_formula_subclauses',
            'repair_packet': 8, 'owner_role': 'analytics_lead', 'contract_boundary': 'analytics-snapshot-repository',
            'depends_on_packets': list(range(1, 8)), 'acceptance_target': 'independent_formula_unavailable_and_export_cases',
            'evidence': [], 'implementation_status': 'UNVERIFIED'})
    handoff = (ROOT / 'docs/strategy/QUALIFICATION_AND_HANDOFF.md').read_text()
    gates = []
    for line in handoff.splitlines():
        match = re.match(r'\| (WP\d{2}|OPS-R\d{2}) \|([^|]+)', line)
        if match:
            gid, text = match.groups()
            gates.append({'id': gid, 'requirement': text.strip(), 'source': 'PDF-05',
                'pages_1based': ([65, 66] if gid.startswith('WP') else [67, 68]),
                'status': 'UNQUALIFIED', 'evidence': [], 'owner_role': 'named_operator_pending'})
    if len(gates) != 25:
        raise ValueError('Missing WP/OPS-R inventory')
    return records, gates


def openapi_inventory():
    base = dotenv_values(ROOT / 'frontend/.env')['REACT_APP_BACKEND_URL'].rstrip('/')
    import subprocess
    spec = json.loads(subprocess.check_output(
        ['curl', '--silent', '--show-error', '--fail', '--max-time', '30', base + '/api/openapi.json'],
        timeout=35,
    ))
    rows = []
    for path, methods in spec['paths'].items():
        for method, operation in methods.items():
            if method not in ('get', 'post', 'put', 'patch', 'delete', 'options', 'head'):
                continue
            required = ('x-owner-policy', 'x-role-scope', 'x-workload-tier', 'x-idempotency-mode', 'x-body-limit-bytes')
            if any(key not in operation for key in required):
                raise ValueError('Runtime route is missing executable contract metadata')
            rows.append({
                'operation_id': operation.get('operationId'), 'method': method.upper(), 'path': path,
                'roles': operation['x-role-scope'], 'workload_tier': operation['x-workload-tier'],
                'owner_policy': operation['x-owner-policy'], 'idempotency_mode': operation['x-idempotency-mode'],
                'body_limit_bytes': operation['x-body-limit-bytes'],
                'status': 'IMPLEMENTED_PILOT_INGRESS_WITH_LIVE_CELL_GAPS',
                'gaps': operation.get('x-known-gaps', []),
                'current_response_models': list(operation.get('responses', {}).keys()),
                'note': 'Copied from mounted route contracts. Auth roles derive from actual dependencies; ownership and transaction correctness require independent tests.',
            })
    spec['info']['description'] = 'Pinned current API inventory; legacy gaps remain. Target /api/v1 aliases are not implemented. Not a full production contract freeze.'
    write('openapi.current.v1.json', spec)
    write('operation_catalogue.v1.json', {'version': 1, 'routes': rows, 'complete_target_contract': False})


def dependencies():
    packages = sorted([{'name': d.metadata.get('Name', 'unknown'), 'version': d.version}
        for d in importlib.metadata.distributions()], key=lambda p: p['name'].lower())
    inputs = {}
    for path in ['backend/requirements.txt', 'frontend/package.json', 'frontend/yarn.lock']:
        full = ROOT / path
        if full.exists():
            inputs[path] = digest(full.read_bytes())
    write('dependency_baseline.json', {'format': 'dependency-inventory-v1', 'signed': False,
        'sbom_attestation': 'NOT_AN_ATTESTED_RELEASE_SBOM', 'python_installed': packages,
        'lockfile_sha256': inputs, 'advisory_status': 'TRIAGE_REQUIRED_NOT_A_CLEAN_SCAN',
        'note': 'Frontend lock hash is inventory, not a transitive CycloneDX/SPDX SBOM or license/security scan'})


def main():
    OUT.mkdir(exist_ok=True)
    sources, pages, blocks = source_inventory()
    from source_review import ReviewLedger, trusted_source_blocks, validate_ledger
    ledger = ReviewLedger.model_validate_json((OUT/'review_ledger.v1.json').read_bytes())
    source_texts, source_pages = trusted_source_blocks()
    reviewed = validate_ledger(ledger, source_texts, source_pages)
    reviewed_ids = {block.block_id for block in ledger.blocks}
    for block in blocks:
        if block['id'] in reviewed_ids:
            block['review_status'] = 'AGENT_PARTITIONED_NOT_INDEPENDENTLY_APPROVED'
    write('evidence/source-review-current.json', reviewed)
    clauses, gates = requirements()
    write('requirements.v1.json', {'version': 1, 'complete': False, 'requirements': clauses})
    write('source_block_inventory.v1.json', {'sources': sources, 'pages': pages, 'blocks': blocks})
    write('release_gates.v1.json', {'version': 1, 'gates': gates})
    write('workload.v1.json', calculate().model_dump())
    write('command_schemas.v1.json', {c.__name__: c.model_json_schema() for c in [CommandIntent, CommandReceipt, ExactMarks, SourceAnchor, CandidateQuestion]})
    coverage = {'version': 1, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'sources': sources, 'page_count': len(pages), 'block_count': len(blocks),
        'indexed_pages': len(pages), 'fully_atomized_reviewed_pages': 0,
        'exact_span_partitioned_pages': reviewed['partitioned_pages'],
        'exact_span_partitioned_blocks': reviewed['partitioned_blocks'],
        'exact_span_bound_requirements': reviewed['bound_requirements'],
        'exact_span_registry': 'docs/packet1/review_ledger.v1.json',
        'reviewed_subset_obligations': len(CLAUSES), 'analysis_feature_obligations': 60,
        'wp_gates': 13, 'ops_r_gates': 12, 'orphan_mandatory_clauses': None,
        'zero_orphan_proven': False, 'packet1_exit': 'BLOCKED',
        'reason': 'Full atomic mandatory-clause review, tests and owner approval remain incomplete. Indexing all pages is not compliance.',
        'registry': 'docs/packet1/requirements.v1.json', 'page_review_queue': 'docs/packet1/source_block_inventory.v1.json'}
    write('coverage_manifest.json', coverage)
    lines = ['# Packet 1 coverage matrix', '', '**BLOCKED: no zero-orphan/complete atomic-coverage claim.**', '',
        f'Indexed {len(pages)} source pages and {len(blocks)} blocks. Fully atomized/reviewed pages: 0. Reviewed subset: {len(CLAUSES)} obligations; 60 analysis feature obligations (formula subclauses still required). All 25 operational gates retained.', '',
        '| ID | Source/pages | Repair packet | Boundary | Acceptance target | Evidence |', '|---|---|---:|---|---|---|']
    for r in clauses:
        lines.append(f'| {r["id"]} | {r["source"]} pp{",".join(map(str, r["pages_1based"]))} | {r["repair_packet"]} | {r["contract_boundary"]} | {r["acceptance_target"]} | UNVERIFIED |')
    lines.extend(['', '## Exact-span agent review (independent approval pending)', '',
        f"{reviewed['partitioned_pages']} pages / {reviewed['partitioned_blocks']} blocks / {reviewed['bound_requirements']} bound requirements. This is not semantic-completeness or capacity proof. Exact quote hashes and offsets are in review_ledger.v1.json.", '',
        '| ID | Obligation | Packet | Acceptance status |', '|---|---|---:|---|'])
    for requirement in ledger.requirements:
        lines.append(f'| {requirement.id} | {requirement.obligation} | {requirement.packet} | PLANNED / NOT QUALIFIED |')
    (OUT / 'COVERAGE_MATRIX.md').write_text('\n'.join(lines) + '\n')
    openapi_inventory()
    dependencies()
    print(json.dumps({'source_pages': len(pages), 'source_blocks': len(blocks), 'subset_requirements': len(clauses), 'release_gates': len(gates), 'packet1_exit': 'BLOCKED'}))


if __name__ == '__main__':
    main()
