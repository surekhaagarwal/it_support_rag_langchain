import csv,json
from dotenv import load_dotenv
from src.ingest import ROOT
from src.retrieval import Search

def hit(ids,gold,k=5):return int(bool(set(ids[:k])&set(gold)))
def rr(ids,gold):return next((1/i for i,x in enumerate(ids,1) if x in gold),0.0)
def main():
    load_dotenv(ROOT/'.env')
    search=Search()
    with (ROOT/'evals/eval_questions.csv').open(newline='') as f:questions=list(csv.DictReader(f))
    report={}
    for mode in ['semantic','bm25','hybrid']:
        rows=[]
        for q in questions:
            if q['answerable'].lower()!='true':continue
            gold=[x.strip() for x in q['gold_ticket_ids'].split(';') if x.strip()]
            ids=[x['id'] for x in search.query(q['question'],mode,5)]
            rows.append({'question_id':q['question_id'],'retrieved':ids,'hit_at_5':hit(ids,gold),'rr_at_5':rr(ids,gold)})
        report[mode]={'hit_rate_at_5':sum(r['hit_at_5'] for r in rows)/len(rows),'mrr_at_5':sum(r['rr_at_5'] for r in rows)/len(rows),'details':rows}
    (ROOT/'evals/retrieval_results.json').write_text(json.dumps(report,indent=2))
    for name,r in report.items():print(name,round(r['hit_rate_at_5'],3),round(r['mrr_at_5'],3))
if __name__=='__main__':main()
