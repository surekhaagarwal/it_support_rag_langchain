import re
from collections import defaultdict
from rank_bm25 import BM25Okapi
from src.ingest import load_chunks, store, validate_index
from src.chunking import load_settings

# Filter conversational filler equally in indexed text and queries. Keep negations,
# product names, error numbers and identifiers such as INC-1027 intact.
STOP_WORDS = set('''a an the is are was were be been being i my me we our you your
it its this that these those what which how when where why who to of for from
in on at by with and or as do does did can could should would will have has had
please previous previously recorded worked before issue problem says'''.split())
CANDIDATE_COUNT = 15
RRF_CONSTANT = 60
MAX_CHUNKS_PER_SOURCE = 2


def tokens(text):
    return [word for word in re.findall(r'[a-z0-9]+(?:[-_.][a-z0-9]+)*', text.lower())
            if word not in STOP_WORDS]


def requested_ids(text):
    """Extract explicit record identifiers from the user search text."""
    return list(dict.fromkeys(value.upper() for value in re.findall(
        r'\b(?:INC|KB)-\d+(?:::chunk-\d+)?\b', text, re.IGNORECASE)))


class Search:
    def __init__(self, settings=None):
        self.settings = settings or load_settings()
        self.docs = load_chunks(self.settings)
        self.bm = BM25Okapi([tokens(d.page_content) for d in self.docs])
        self.vectors = store(self.settings)
        validate_index(self.vectors, self.docs, self.settings)

    def semantic(self, q, k=5):
        # The index uses cosine distance. Similarity = 1 - distance.
        return [{'id': d.metadata.get('chunk_id', d.metadata['source_id']),
                 'source_id': d.metadata['source_id'], 'doc': d,
                 'distance': float(distance), 'similarity': 1 - float(distance)}
                for d, distance in self.vectors.similarity_search_with_score(q, k=k)]

    def keyword(self, q, k=5):
        scores = self.bm.get_scores(tokens(q))
        ranks = sorted(enumerate(scores), key=lambda item: item[1], reverse=True)
        return [{'id': self.docs[i].metadata.get('chunk_id', self.docs[i].metadata['source_id']),
                 'source_id': self.docs[i].metadata['source_id'], 'doc': self.docs[i],
                 'bm25_score': float(score)} for i, score in ranks[:k] if score > 0]

    def query(self, q, mode='hybrid', k=5):
        if mode == 'semantic':
            return self.semantic(q, k)
        if mode == 'bm25':
            return self.keyword(q, k)
        comparison = self.compare(q, k)
        if comparison.get('error'):
            raise RuntimeError(comparison['error'])
        return comparison['hybrid']

    def compare(self, q, k=5):
        """Retrieve once per method; comparisons share the answer's candidates."""
        count = min(max(CANDIDATE_COUNT, k), len(self.docs))
        b = self.keyword(q, count)
        try:
            a = self.semantic(q, count)
        except Exception:
            return {'semantic': [], 'bm25': b[:k], 'hybrid': [],
                    'error': 'Semantic search is unavailable; hybrid results cannot be computed.'}
        return {'semantic': a[:k], 'bm25': b[:k], 'hybrid': self.hybrid(q, a, b, k)}

    def hybrid(self, q, a, b, k=5):
        # Rank the union before diversification, so lower-ranked sources can fill
        # slots freed by repeated article chunks.
        ranked = self.fuse(a, b, len(a) + len(b))
        pinned = []
        for identifier in requested_ids(q):
            # Prefer the best retrieved passage for a parent article. If the
            # requested record was absent from both lists, find it by metadata.
            matches = [row for row in ranked if identifier in
                       (row['id'].upper(), row.get('source_id', row['id']).upper())]
            if matches:
                pinned.append(dict(matches[0], exact_id_match=True))
                continue
            document = next((d for d in self.docs if identifier in
                             (d.metadata.get('chunk_id', '').upper(),
                              d.metadata.get('source_id', '').upper())), None)
            if document is not None:
                pinned.append({'id': document.metadata.get('chunk_id', document.metadata['source_id']),
                               'source_id': document.metadata['source_id'], 'doc': document,
                               'exact_id_match': True})
        hybrid = []
        seen = set()
        counts = defaultdict(int)
        for row in pinned + ranked:
            parent = row.get('source_id', row['id'])
            if row['id'] in seen or counts[parent] >= MAX_CHUNKS_PER_SOURCE:
                continue
            hybrid.append(row)
            seen.add(row['id'])
            counts[parent] += 1
            if len(hybrid) >= k:
                break
        return hybrid

    @staticmethod
    def fuse(a, b, k=5):
        scores = defaultdict(float)
        lookup = {}
        for results in (a, b):
            for rank, item in enumerate(results, 1):
                scores[item['id']] += 1 / (RRF_CONSTANT + rank)
                lookup.setdefault(item['id'], {}).update(item)
        return [dict(lookup[id], rrf_score=scores[id])
                for id in sorted(scores, key=scores.get, reverse=True)[:k]]
