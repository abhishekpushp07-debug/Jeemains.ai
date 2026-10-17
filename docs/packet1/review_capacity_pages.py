"""Manually reviewed source recipes for PDF-05 pp3/55 ONLY.

Not an automatic semantic classifier. Every cut is checked against the original
hash-bound text. Existing other-page reviews are preserved; unknown drift fails.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
from source_review import ROOT, ReviewLedger, trusted_source_blocks, validate_ledger, sha

# Each segment starts at an exact substring of its source block. An empty start
# means offset zero. Obligations below were reviewed against the original PDF.
RECIPES = {
 (3,3): [
  ('','Use one shared workload model across architecture, testing and cost calculations',1),
  ('It is a','Treat the workload as a proposed planning model, not measured capacity',1),
  ('Record observed','Record observed student behavior and revise the model before claiming capacity',10),
  ('The nominal','Use 10800 seconds as the nominal planning exam duration',1),
  ('actual exam','Keep actual exam duration configuration-driven',6)],
 (3,6): [('', 'Model 500000 commitments per30seconds as 16666.7 requests/second',1),('Critical, durable','Keep explicit commitments in the critical durable lane',6)],
 (3,7): [('', 'Model20percent dirty drafts per10seconds as10000 requests/second',1),('Recoverable draft','Classify drafts as recoverable writes, not grading commitments',6)],
 (3,8): [('', 'Model independent leases for500000 sessions per60seconds as8333.3 requests/second',1),('Critical control','Reserve the critical control lane for lease work',2)],
 (3,9): [('', 'Model35000 live requests/second before coalescing',1)],
 (3,10): [('', 'Model500000 telemetry batches per30seconds as16666.7 batches/second',1),('Separate bounded','Isolate telemetry in a separate bounded lane',8)],
 (3,11): [('', 'Model51666.7 normal combined requests/second',1),('Excludes CDN','Account for CDN asset hits separately from baseline API traffic',10)],
 (3,12): [('', 'Model all-dirty drafts every5seconds plus commits and leases as the125000-live-request pathological scenario',1)],
 (3,13): [('', 'Model all-dirty drafts every5seconds plus commits and leases as the125000-live-request pathological scenario',1)],
 (3,15): [
  ('','Qualify two-times normal live throughput of70000 requests/second',10),
  ('and 33,333.3','Qualify two-times telemetry throughput of33333.3 batches/second',10),
  ('This headroom','Do not infer pathological workload success from two-times normal headroom',10),
  ('test that case separately','Test the pathological workload separately',10),
  ('coalesce recoverable','Coalesce recoverable work while preserving eligible commitments',6),
  ('Requests, database','Keep API requests, transactions, response rows, events and storage IOPS as distinct units',1)],
 (3,16): [
  ('','Model500000 starts over120seconds as4166.7 starts/second',1),
  ('and 500,000 submissions','Model500000 submissions over30seconds as16666.7 submissions/second',1),
  ('A two-megabyte','Model2MB packages across500000students as1TB edge delivery and66.667Gbit/s over120seconds before overhead',1),
  ('State decimal units','State decimal byte and bandwidth units in capacity evidence',10),
  ('cache assumptions','State cache assumptions in capacity evidence',10),
  ('and whether assets','Disclose whether package assets are prefetched in the measured run',10)],
 (3,18): [('', 'Measure per-cell write amplification and index overhead rather than equating API RPS with DB TPS',10)],
 (3,19): [('', 'Treat20cells of25000activeattempts as a proposed partition, not measured capacity',1)],
 (55,3): [
  ('','Qualify500000 concurrently active sessions for a full three-hour exam workload',10),
  ('This target means','Use distinct authenticated attempts exercising reading, changes, commits, leases and submit, not idle or registered users',10),
  ('Treat every number','Require measured evidence and operator signoff for proposed acceptance targets',10)],
 (55,5): [
  ('','Use20proposed cells with at most25000admitted active attempts per qualified cell',2),
  ('Freeze\nthe cell','Freeze resource specification, database variant, pools, versions, route distribution and exam mix in the run manifest',10),
  ('Qualify two times','Qualify twice each cell baseline mix as proposed headroom',10),
  ('then test the defined','Test the declared bursts and failure scenarios separately',10),
  ('Do not describe','Never describe spare capacity, autoscaling limits or small-test success as guaranteed500000capacity',10),
  ('Name the exact','Name the exact database deployment variant in evidence',2),
  ('Multi-AZ instances','Do not assign an unverified shared replication promise to distinct database deployment variants',2)],
 (55,6): [
  ('','Protect admitted sessions while reducing new admissions',2),
  ('Capacity approval must identify','Identify which covered failures preserve acknowledged writes in capacity approval',10),
  ('and which regional disasters','Disclose regional disasters that can lose asynchronously replicated data',10),
  ('A page declaring','Display Saved only for a durable committed response, never draft/cache/queue acceptance alone',7)],
 (55,8): [
  ('','Measure valid commit in-region ingress-to-durable-ack p95 at most300ms',10),
  ('and p99 <=','Measure valid commit ingress-to-durable-ack p99 at most1000ms including queueing and persistence',10),
  ('Separately measure','Separately measure client round-trip and rendered save feedback on representative Indian networks',10),
  ('report\nthose values','Do not relabel server processing time as total student latency',10),
  ('Operators must approve','Obtain operator approval of a separate client-experience budget before launch',10)],
 (55,9): [
  ('','Require durable submission receipt p99 at most2seconds under the declared submission burst',10),
  ('Measure\nreceipt-to-correct','Require receipt-to-correct-core-grade readiness p95 at most60seconds',10),
  ('and p99 <=','Require receipt-to-correct-core-grade readiness p99 at most120seconds; a visible pending grade is allowed meanwhile',10),
  ('Server errors must','Require server errors at most0.1percent across the full run',10),
  ('and within each','Require server errors at most0.1percent inside every predeclared critical window',10),
  ('Integrity constraints','Allow zero wrong grades within the covered failure envelope',6),
  ('duplicate score effects','Allow zero duplicate score effects within the covered failure envelope',6),
  ('or lost acknowledged','Allow zero lost acknowledged commits within the covered failure envelope',6)],
 (55,11): [
  ('','Distinguish correctness, API performance, browser behavior, connection capacity and disaster recovery evidence',10),
  ('Publish actual','Publish achieved load and shortfalls',10),
  ('Never call','Never pass an interrupted, under-generated or reduced-activity run',10),
  ('Keep the same','Use identical endpoint and timing definitions in generators, dashboards and release decisions',10)],
 (55,13): [('', 'Version the workload, SLO definitions and failure envelope',1)],
 (55,14): [('', 'Require both qualified-cell and global-run approval decisions',10)],
 (55,15): [('', 'Preserve admitted-session write capacity during admission throttling',2)],
}
LAYOUT = {(3,i) for i in [0,1,2,4,5,14,17,20]} | {(55,i) for i in [0,1,2,4,7,10,12,16]}


def main():
    texts,pages=trusted_source_blocks()
    target_ids={bid for bid in texts if bid.startswith(('PDF05-P003-','PDF05-P055-'))}
    declared={f'PDF05-P{p:03d}-B{b:03d}' for p,b in set(RECIPES)|LAYOUT}
    if target_ids != declared:
        raise ValueError('Source layout changed; manual review required')
    path=ROOT/'docs/packet1/review_ledger.v1.json'
    old=ReviewLedger.model_validate_json(path.read_bytes())
    kept_blocks=[b.model_dump(mode='json') for b in old.blocks if b.block_id not in target_ids]
    retained_ids={s['requirement_id'] for b in kept_blocks for s in b['spans'] if s.get('requirement_id')}
    requirements=[r.model_dump(mode='json') for r in old.requirements if r.id in retained_ids]
    seen={}
    stamp=datetime.now(timezone.utc).isoformat()
    for bid in sorted(target_ids):
        page=int(bid[7:10]); block=int(bid[12:15]); text=texts[bid]
        spans=[]
        if (page,block) in LAYOUT:
            spans=[{'start_codepoint':0,'end_codepoint':len(text),'quote_sha256':sha(text),
                    'kind':'layout','requirement_id':None,
                    'rationale':'Reviewed repeated branding, section heading, table column labels or source footer; numerical obligations are bound in adjacent normative blocks.'}]
        else:
            recipes=RECIPES[(page,block)]
            offsets=[0]
            for start,_,_ in recipes[1:]:
                found=text.find(start,offsets[-1]+1)
                if found < 0:
                    raise ValueError('Manual source cut no longer matches')
                offsets.append(found)
            offsets.append(len(text))
            for index,(_,obligation,packet) in enumerate(recipes):
                if obligation in seen:
                    rid=seen[obligation]
                else:
                    rid=f'SRC05-P{page:03d}-B{block:03d}-R{index+1:02d}'
                    seen[obligation]=rid
                    requirements.append({'id':rid,'obligation':obligation,'packet':packet,
                        'owner_role':'performance_operator' if packet==10 else 'application_lead',
                        'boundaries':['workload-and-slo-contract' if page==3 or packet==10 else 'admission-or-exam-authority'],
                        'acceptance_cases':['planned:independent.source-clause.'+rid],
                        'evidence':[], 'semantic_review':'AGENT_REVIEWED_NOT_OPERATOR_APPROVED'})
                start,end=offsets[index:index+2]
                spans.append({'start_codepoint':start,'end_codepoint':end,'quote_sha256':sha(text[start:end]),
                              'kind':'requirement','requirement_id':rid,'rationale':''})
        kept_blocks.append({'block_id':bid,'original_text_sha256':sha(text),'reviewed_at':stamp,
                            'reviewer_role':'engineering_agent','spans':spans})
    ledger=ReviewLedger.model_validate_json(json.dumps({'schema_version':'source-review-v1','requirements':requirements,'blocks':kept_blocks}))
    result=validate_ledger(ledger,texts,pages)
    path.write_text(ledger.model_dump_json(indent=2)+'\n')
    (ROOT/'docs/packet1/evidence/source-review-current.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('remaining_block_ids','note')}))


if __name__=='__main__':
    main()
