"""Fresh retrieval evaluation for the Streamlit evaluation page.

Only benchmark CSV inputs are read. Results are returned to the caller, never
loaded from prior reports or written to disk.
"""
import csv
from datetime import datetime, timezone
from time import perf_counter

from src.ingest import ROOT, fingerprint
from src.retrieval import Search, CANDIDATE_COUNT, RRF_CONSTANT, MAX_CHUNKS_PER_SOURCE

SUITES = {
    'Main benchmark (21 questions)': ('eval_questions.csv', 'kb_questions.csv'),
    'Held-out benchmark (10 questions)': ('hybrid_holdout.csv',),
}
METHODS = ('semantic', 'bm25', 'hybrid')
LABELS = {'semantic': 'Semantic', 'bm25': 'BM25', 'hybrid': 'Hybrid'}


def hit(ids, gold, k=5):
    return int(bool(set(ids[:k]) & set(gold)))


def rr(ids, gold):
    return next((1 / rank for rank, source in enumerate(ids[:5], 1) if source in gold), 0.0)


def load_benchmark(suite):
    questions = []
    for filename in SUITES[suite]:
        with (ROOT / 'evals' / filename).open(newline='') as stream:
            for row in csv.DictReader(stream):
                if row['answerable'].lower() != 'true':
                    continue
                gold = [value.strip() for value in row['gold_ticket_ids'].split(';') if value.strip()]
                if not gold:
                    raise ValueError(f"Question {row['question_id']} has no expected sources.")
                questions.append({'id': row['question_id'], 'question': row['question'], 'gold': gold})
    if not questions:
        raise ValueError('The selected benchmark has no labeled, answerable questions.')
    return questions


def run_benchmark(suite, progress=None):
    """Create a fresh retriever; compare once per question for shared candidates."""
    questions = load_benchmark(suite)
    start = perf_counter()
    search = Search()
    rows = []
    for index, question in enumerate(questions, 1):
        results = search.compare(question['question'], k=5)
        if results.get('error'):
            raise RuntimeError(results['error'])
        methods = {}
        for method in METHODS:
            found = results[method]
            parents = [item.get('source_id', item['id']) for item in found]
            methods[method] = {
                'retrieved_ids': [item['id'] for item in found],
                'parent_sources': parents,
                'hit_at_5': hit(parents, question['gold']),
                'rr_at_5': rr(parents, question['gold']),
            }
        rows.append({**question, 'methods': methods})
        if progress:
            progress(index, len(questions))
    summary = {method: {
        'hits': sum(row['methods'][method]['hit_at_5'] for row in rows),
        'hit_rate_at_5': sum(row['methods'][method]['hit_at_5'] for row in rows) / len(rows),
        'mrr_at_5': sum(row['methods'][method]['rr_at_5'] for row in rows) / len(rows),
    } for method in METHODS}
    return {
        'suite': suite, 'profile': search.settings.profile,
        'fingerprint': fingerprint(search.docs, search.settings),
        'completed_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'duration_seconds': round(perf_counter() - start, 2),
        'question_count': len(rows), 'summary': summary, 'rows': rows,
        'settings': {'candidates_per_method': CANDIDATE_COUNT,
                     'rrf_constant': RRF_CONSTANT, 'max_chunks_per_source': MAX_CHUNKS_PER_SOURCE},
    }
