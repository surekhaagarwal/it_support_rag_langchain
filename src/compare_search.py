
import json
import re
from pathlib import Path
from dotenv import load_dotenv


from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

def tokenize(text):
    return re.findall(
        r"[a-z0-9]+",
        text.lower()
    )

# Load your JSON records
with open(ROOT / "data" / "incidents.json") as f:
    incidents = json.load(f)

with open(ROOT / "data" / "knowledge_base.json") as f:
    knowledge_base = json.load(f)


# Use the same text formatting as ingestion
documents = []

# Load incidents
with open(ROOT / "data" / "incidents.json", encoding="utf-8") as f:
    incidents = json.load(f)

for incident in incidents:
    text = f"""
    Title: {incident.get('title', '')}
    Symptoms: {incident.get('symptoms', '')}
    Error Code: {incident.get('error_code', '')}
    Root Cause: {incident.get('root_cause', '')}
    Resolution: {incident.get('resolution', '')}
    """

    documents.append(
        Document(
            page_content=text.strip(),
            metadata={
                "id": incident["ticket_id"],
                "category": incident.get("category", ""),
                "type": "incident"
            }
        )
    )

# Load knowledge base
with open(ROOT / "data" / "knowledge_base.json", encoding="utf-8") as f:
    knowledge_base = json.load(f)

for kb in knowledge_base:
    text = f"""
    Title: {kb.get('title', '')}
    Summary: {kb.get('synthetic_summary', '')}
    """

    documents.append(
        Document(
            page_content=text.strip(),
            metadata={
                "id": kb["kb_id"],
                "category": kb.get("category", ""),
                "type": "knowledge_base"
            }
        )
    )

#print(f"Loaded {len(incidents)} incidents")
#print(f"Loaded {len(knowledge_base)} knowledge articles")
#print(f"Total documents: {len(documents)}")


# BM25 indexing
tokenized = [
    tokenize(doc.page_content)
    for doc in documents
]

bm25 = BM25Okapi(tokenized)


#print("\n========== BM25 INDEX CHECK ==========")

#print("Total documents:", len(documents))
#print("BM25 indexed documents:", len(bm25.doc_len))

#incident_count = sum(
 #   1 for doc in documents
  #  if doc.metadata["id"].startswith("INC-")
#)

# k""" b_count = sum(
#     1 for doc in documents
#     if doc.metadata["id"].startswith("KB-")
# )

# print("Incidents:", incident_count)
# print("Knowledge articles:", kb_count)

# print("First document ID:", documents[0].metadata["id"])
# print("Last document ID:", documents[-1].metadata["id"]) """


# Connect to existing Chroma collection
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

vectorstore = Chroma(
    collection_name="it_support_v1",
    persist_directory=str(ROOT / "chroma_db"),
    embedding_function=embeddings
)


def semantic_search(query, k=5):
    results = vectorstore.similarity_search_with_score(
        query,
        k=k
    )

    retrieved = []

    for doc, distance in results:
        metadata = doc.metadata

        doc_id = (
            metadata.get("id")
            or metadata.get("ticket_id")
            or metadata.get("kb_id")
            or metadata.get("source_id")
        )

        if not doc_id:
            raise ValueError(
                f"Missing document ID in metadata: {metadata}"
            )

        retrieved.append(
            (doc_id, 1 - distance)
        )

    return retrieved


def keyword_search(query, k=5):
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(
        enumerate(scores),
        key=lambda x: x[1],
        reverse=True
    )[:k]

    return [
        (documents[i].metadata["id"], float(score))
        for i, score in ranked
    ]


def hybrid_search(query, k=5, rrf_k=60):
    semantic = semantic_search(query, k=10)
    keyword = keyword_search(query, k=10)

    fused = {}

    for results in [semantic, keyword]:
        seen = set()

        for rank, (doc_id, _) in enumerate(results, 1):
            if doc_id is None:
                raise ValueError(
                    "Missing document ID in retrieval results"
                )

            if doc_id in seen:
                continue

            seen.add(doc_id)

            fused[doc_id] = (
                fused.get(doc_id, 0)
                + 1 / (rrf_k + rank)
            )

    return sorted(
        fused.items(),
        key=lambda x: x[1],
        reverse=True
    )[:k]


question = (
    "What resolved VPN error 789?"
)
print("The question is",question)
for name, search_fn in [
    ("Semantic", semantic_search),
    ("BM25", keyword_search),
    ("Hybrid", hybrid_search)
]:
    print(f"\n{name.upper()} RESULTS")
    for rank, (doc_id, score) in enumerate(
        search_fn(question), 1
    ):
        print(f"{rank}. {doc_id} | Score: {score:.4f}")
