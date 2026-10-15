
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

vectorstore = Chroma(
    persist_directory=str(ROOT / "chroma_db"),
    embedding_function=embeddings,
    collection_name="it_support_v1"
)

question = (
    "My VPN disconnects when switching Wi-Fi networks. "
    "How was this resolved previously?"
)

results = vectorstore.similarity_search_with_score(
    question,
    k=5
)

print("\nSEMANTIC SEARCH RESULTS")

for rank, (doc, distance) in enumerate(results, start=1):
    print(f"\nRank: {rank}")
    print(f"Source: {doc.metadata}")
    print(f"Cosine distance: {distance:.4f}")
    print(f"Similarity: {1 - distance:.4f}")
    print(f"Text: {doc.page_content[:300]}")
