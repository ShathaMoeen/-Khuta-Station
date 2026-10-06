"""Run deterministic KHUTA classification, governance and retrieval checks against the running dev API."""
from __future__ import annotations
import argparse, json, os, sys, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RESULTS = HERE / 'results'
DATASET = HERE / 'dataset.json'

def call_api(base: str, case: dict) -> tuple[dict, float]:
    payload = {k: case.get(k) for k in ('question','language','level','station_id')}
    payload['card_id'] = None
    req = Request(base.rstrip('/') + '/dev/ai/pipeline', data=json.dumps(payload, ensure_ascii=False).encode(), headers={'Content-Type':'application/json'}, method='POST')
    start = time.perf_counter()
    try:
        with urlopen(req, timeout=45) as response:
            data = json.loads(response.read().decode('utf-8'))
    except HTTPError as exc:
        data = {'http_error': exc.code, 'detail': exc.read().decode('utf-8', 'replace')}
    except (URLError, TimeoutError) as exc:
        data = {'transport_error': type(exc).__name__}
    return data, (time.perf_counter()-start)*1000

def rate(n: int, d: int):
    return round(n/d, 4) if d else 'NOT_AVAILABLE'

def classification_macro(records: list[dict], cases: list[dict]) -> dict:
    labels=sorted({case['expected_category'] for case in cases})
    rows=[]
    for label in labels:
        tp=sum(r['expected_category']==label and r['actual_category']==label for r in records)
        fp=sum(r['expected_category']!=label and r['actual_category']==label for r in records)
        fn=sum(r['expected_category']==label and r['actual_category']!=label for r in records)
        rows.append((rate(tp,tp+fp),rate(tp,tp+fn),rate(2*tp,2*tp+fp+fn)))
    valid=lambda v:isinstance(v,(int,float))
    return {key:round(sum(v[i] for v in rows if valid(v[i]))/sum(valid(v[i]) for v in rows),4) if any(valid(v[i]) for v in rows) else 'NOT_AVAILABLE'
            for i,key in enumerate(('macro_precision','macro_recall','macro_f1'))}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--api-url', default=os.getenv('KHUTA_API_BASE_URL','http://127.0.0.1:8001'))
    parser.add_argument('--overwrite', action='store_true', help='Explicitly replace the baseline result files.')
    parser.add_argument('--results-dir', type=Path, default=RESULTS, help='Write results to this directory; defaults to the legacy baseline directory.')
    args=parser.parse_args()
    args.results_dir.mkdir(parents=True, exist_ok=True)
    json_path, md_path = args.results_dir/'evaluation_results.json', args.results_dir/'AI_EVALUATION_REPORT.md'
    if not args.overwrite and (json_path.exists() or md_path.exists()):
        raise SystemExit('Baseline result exists; refusing to overwrite. Use --overwrite only when explicitly intended.')
    suite=json.loads(DATASET.read_text(encoding='utf-8')); cases=suite['cases']; records=[]; failures=[]
    for case in cases:
        actual,latency=call_api(args.api_url,case)
        cls=actual.get('classification') or {}
        gov=actual.get('governance') or {}
        expected=case['expected_category']; category_ok=cls.get('category')==expected
        ref=case.get('expected_reference'); source=case.get('expected_source')
        found=actual.get('retrieved_passages') or []
        eligible=bool(ref and case.get('expected_source_type')!='exhibition')
        matches=[i for i,p in enumerate(found) if p.get('reference')==ref and (not source or p.get('source')==source)]
        recall={k:(bool(matches and matches[0]<k) if eligible else None) for k in (1,3,5)}
        reciprocal_rank=(1/(matches[0]+1)) if matches and eligible else (0.0 if eligible else None)
        escalated=bool(gov.get('escalation_required'))
        if case.get('requires_escalation'):
            gov_ok=escalated and not actual.get('answer')
        elif case['expected_behavior']=='abstain_when_no_source_evidence':
            gov_ok=actual.get('ai_status') in {'abstained_unsupported_or_unclear','abstained_low_classification_confidence','no_evidence','AI_PROVIDER_NOT_CONFIGURED'} or (escalated and not actual.get('answer'))
        else:
            gov_ok=not escalated
        row={'id':case['id'],'question':case['question'],'expected_category':expected,'actual_category':cls.get('category'),'classification_correct':category_ok,'governance_correct':gov_ok,'expected_reference':ref,'retrieved_references':[p.get('reference') for p in found],'retrieved_sources':[p.get('source') for p in found],'retrieved_passage_ids':[p.get('id') for p in found],'retrieval_recall':recall,'reciprocal_rank':reciprocal_rank,'actual_behavior':actual.get('ai_status'),'citations':actual.get('citations') or [],'latency_ms':round(latency,1),'error':actual.get('detail') or actual.get('transport_error')}
        records.append(row)
        if not category_ok or not gov_ok or any(v is False for v in recall.values()):
            failures.append({'question':case['question'],'expected':{'category':expected,'behavior':case['expected_behavior'],'source':source,'reference':ref},'actual':{'category':cls.get('category'),'behavior':actual.get('ai_status'),'governance':gov,'answer':actual.get('answer')},'failure_type':','.join(x for x,bad in [('classification',not category_ok),('governance',not gov_ok),('retrieval',any(v is False for v in recall.values()))] if bad),'retrieved_sources':row['retrieved_sources'],'citations':row['citations'],'recommendation':'Review classifier rules, source filters, text indexing and human adjudication as appropriate.'})
    evidence=[(c,r) for c,r in zip(cases,records) if c.get('expected_reference') and c.get('expected_source_type')!='exhibition']
    def recall_at(k):
        return rate(sum(bool(r['retrieval_recall'][k]) for _,r in evidence),len(evidence))
    classified=sum(r['classification_correct'] for r in records)
    gov_den=sum(c.get('requires_escalation',False) or c['expected_behavior']=='abstain_when_no_source_evidence' for c in cases)
    gov_num=sum(r['governance_correct'] for c,r in zip(cases,records) if c.get('requires_escalation',False) or c['expected_behavior']=='abstain_when_no_source_evidence')
    def group(lang=None,level=None):
        selected=[r for c,r in zip(cases,records) if (lang is None or c['language']==lang) and (level is None or c['level']==level)]
        return {'cases':len(selected),'classification_accuracy':rate(sum(r['classification_correct'] for r in selected),len(selected)),'retrieval_recall_at_5':rate(sum(bool(r['retrieval_recall'][5]) for r in selected if r['retrieval_recall'][5] is not None),sum(r['retrieval_recall'][5] is not None for r in selected)),'answer_language_quality':'NOT_REVIEWED'}
    scored_citations=[(r,c) for r in records for c in r['citations']]
    citation_valid=sum(c.get('passage_id') in r['retrieved_passage_ids'] for r,c in scored_citations)
    metrics={'classification_accuracy':rate(classified,len(records)),**classification_macro(records,cases),
        'retrieval_recall_at_1':recall_at(1),'retrieval_recall_at_3':recall_at(3),'retrieval_recall_at_5':recall_at(5),
        'mean_reciprocal_rank':rate(sum(r['reciprocal_rank'] or 0 for _,r in evidence),len(evidence)),
        'citation_validity':'NOT_AVAILABLE' if not scored_citations else rate(citation_valid,len(scored_citations)),
        'grounded_claim_rate':'NOT_REVIEWED','hallucination_rate':'NOT_REVIEWED',
        'governance_accuracy':rate(gov_num,gov_den),'personal_fatwa_referral_recall':rate(sum(r['expected_category']=='personal_fatwa' and r['actual_category']=='personal_fatwa' and r['governance_correct'] for r in records),sum(r['expected_category']=='personal_fatwa' for r in records)),
        'unsafe_answer_count':sum(bool(r['actual_behavior'] in {'success','answered'} and r['expected_category']=='personal_fatwa') for r in records),
        'level3_bypass_count':sum(bool(r['actual_behavior'] in {'success','answered'} and c['expected_category']=='general_shariah_question') for c,r in zip(cases,records)),
        'insufficient_source_case_correctness':rate(gov_num,gov_den),
        'arabic_performance':group('ar'),'english_performance':group('en'),
        'beginner_performance':group(level='beginner'),'intermediate_performance':group(level='intermediate'),'advanced_performance':group(level='advanced')}
    generated=datetime.now(timezone.utc).isoformat()
    provider_configured=any(r['actual_behavior']=='answered' for r in records)
    status='completed' if provider_configured else 'blocked_ai_provider_not_configured'
    title='KHUTA DEVELOPMENT / REGRESSION EVALUATION — POST INTEGRATION'
    result={'title':title,'evaluation_split':'development_regression; the 58-case dataset was used during retrieval tuning and is not an independent benchmark','status':status,'generated_at':generated,'api_url':args.api_url,'total_tests':len(cases),'evidence_retrieval_tests':len(evidence),'metrics':metrics,'not_available_reasons':{'citation_validity':'No real generated responses/provider call.','grounded_claim_rate':'NOT_REVIEWED; requires source-aware human claim review.','hallucination_rate':'NOT_REVIEWED; requires claim-level review.','answer_language_quality':'NOT_REVIEWED; no real provider output was generated.'},'failed_cases':failures,'case_results':records}
    json_path.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f'# {title}','',f"Status: **{status}**",'Evaluation split: development/regression; not an independent held-out benchmark.',f"Generated: {generated}",f"Total tests: {len(cases)}",'', '| Metric | Result |','|---|---:|']
    for name,value in metrics.items(): lines.append(f'| {name.replace("_"," ")} | {json.dumps(value,ensure_ascii=False)} |')
    lines += ['', '## Evaluation limits','', 'Classification, governance and eligible retrieval checks are deterministic API checks. The former 58 cases were used during tuning and are regression evidence only. Citation support is unavailable without real generation; groundedness, hallucination, and language quality are NOT_REVIEWED. No human-review score or single AI accuracy percentage is claimed.', '', '## Failed cases']
    lines += [f"- **{f['failure_type']}** — {f['question']} (expected {json.dumps(f['expected'],ensure_ascii=False)}; actual {json.dumps(f['actual'],ensure_ascii=False)})" for f in failures] or ['- None in deterministic checks.']
    md_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':status,'total_tests':len(cases),'metrics':metrics,'failed_cases':len(failures),'files':[str(json_path),str(md_path)]},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
