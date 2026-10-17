"""Summarize retained dependency scanner evidence without claiming clean/reachable.

Run after both scans; does not install/fix dependencies or invoke external APIs.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from packaging.version import Version, InvalidVersion

ROOT=Path(__file__).resolve().parents[2]
EVIDENCE=ROOT/'docs/packet1/evidence'
OWNERS={
 'pymongo':2,'starlette':4,'python-multipart':4,'pillow':4,'requests':4,'urllib3':4,
 'pyjwt':3,'cryptography':3,'ecdsa':3,'python-jose':3,'pyasn1':3,'idna':3,
 'pytest':1,'black':1,'pygments':1,
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    python_path=EVIDENCE/'python-dependency-audit-current.json'
    if not python_path.exists():
        python_path=EVIDENCE/'python-dependency-audit.json'
    js_path=EVIDENCE/'frontend-dependency-audit-current.jsonl'
    if not js_path.exists():
        js_path=EVIDENCE/'frontend-dependency-audit.jsonl'
    dependencies=json.loads(python_path.read_text())['dependencies']
    affected=[]; skipped=[]
    for dep in dependencies:
        if dep.get('skip_reason'):
            skipped.append({'package':dep['name'],'reason':dep['skip_reason']})
        if not dep.get('vulns'):
            continue
        fixes=sorted({v for finding in dep['vulns'] for v in finding.get('fix_versions',[])},key=Version)
        affected.append({'package':dep['name'],'installed':dep.get('version'),
            'advisory_record_count':len(dep['vulns']), 'advisory_ids':sorted(v['id'] for v in dep['vulns']),
            'listed_fixed_versions':fixes,'no_fix_listed_for_some_findings':any(not v.get('fix_versions') for v in dep['vulns']),
            'owning_packet':OWNERS.get(dep['name'],10),
            'triage':'OPEN_COMPATIBILITY_AND_REACHABILITY_REVIEW_REQUIRED',
            'note':'Scanner records may share aliases. A listed fix is not a tested compatible upgrade; absence of direct imports is not proof of non-reachability.'})
    advisories={}; js_errors=[]
    for line in js_path.read_text().splitlines():
        try: row=json.loads(line)
        except ValueError: continue
        if row.get('type')=='auditAdvisory':
            a=row['data']['advisory']
            advisories[str(a['id'])]={'package':a['module_name'],'severity':a['severity'],
                'url':a.get('url'),'patched_versions':a.get('patched_versions'),'owning_packet':7,
                'triage':'OPEN_RUNTIME_VS_BUILD_REACHABILITY_AND_UPGRADE_REVIEW'}
        elif row.get('type')=='error':
            js_errors.append('Scanner reported an error; see retained artifact')
    counts={level:sum(a['severity']==level for a in advisories.values()) for level in ('critical','high','moderate','low')}
    result={'schema_version':'dependency-triage-v1','recorded_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'OPEN_FINDINGS_NOT_A_CLEAN_SCAN','release_allowed':False,'signed_sbom':False,
        'backend':{'scanner':'pip-audit','dependency_rows':len(dependencies),'affected_packages':affected,
                   'advisory_records':sum(len(d.get('vulns',[])) for d in dependencies),'unscanned':skipped},
        'frontend':{'scanner':'yarn audit --groups dependencies','unique_advisories':advisories,
                    'severity_counts':counts,'scanner_errors':js_errors},
        'artifact_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [python_path,js_path,ROOT/'backend/requirements.txt',ROOT/'frontend/yarn.lock']},
        'requirements':['All unresolved findings need a tested fix or explicit justified security disposition before release',
            'Two skipped Python packages require separate analysis; never treat skip as safe',
            'Upload holds mitigate a route, not a vulnerable package or all parsing call sites',
            'Major FastAPI/Starlette/Motor/PyMongo upgrades require a compatible combination and full regressions',
            'No vulnerability was silently suppressed, auto-fixed, or labelled non-exploitable by this summary']}
    (ROOT/'docs/packet1/dependency_triage.v1.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'backend_affected_packages':len(affected),'backend_advisory_records':result['backend']['advisory_records'],
                     'unscanned_package_count':len(skipped),'frontend_unique_advisories':len(advisories),'frontend_severity_counts':counts,'release_allowed':False}))


if __name__=='__main__':
    main()
