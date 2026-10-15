from pathlib import Path
import chromadb

# Go one level up from src to project root
ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "chroma_db"

print("Database location:", DB_PATH)

# Confirm the database exists before opening it
if not (DB_PATH / "chroma.sqlite3").exists():
    raise FileNotFoundError(
        f"Chroma database not found at {DB_PATH}"
    )

client = chromadb.PersistentClient(path=str(DB_PATH))

collections = client.list_collections()

print("\nAvailable collections:")

for collection in collections:
    print(f"Collection: {collection.name}")
    print(f"Records: {collection.count()}")

    results = collection.get(
        limit=3,
        include=["documents", "metadatas"]
    )

    for i, doc_id in enumerate(results["ids"]):
        print("\n" + "=" * 50)
        print("Document ID:", doc_id)
        print("Metadata:", results["metadatas"][i])
        print("Indexed text:")
        print(results["documents"][i][:500])
