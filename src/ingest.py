import argparse
import hashlib
import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.chunking import (add_chunk_arguments, chunk_documents, load_settings,
                          save_settings, settings_from_args)
ROOT = Path(__file__).resolve().parents[1]
DB = str(ROOT / 'chroma_db')
NAME = 'it_support_v2'

def load_docs():
    incidents = json.loads((ROOT/'data/incidents.json').read_text())
    kb = json.loads((ROOT/'data/knowledge_base.json').read_text())
    docs=[]
    for x in incidents:
        content='\n'.join(f'{key}: {x.get(key, "")}' for key in ['ticket_id','category','title','symptoms','error_code','root_cause','resolution','environment'])
        docs.append(Document(page_content=content,metadata={'source_id':x['ticket_id'],'type':'incident','category':x['category']}))
    for x in kb:
        content='\n'.join(f'{key}: {x.get(key, "")}' for key in ['kb_id','category','title','synthetic_summary'])
        docs.append(Document(page_content=content,metadata={'source_id':x['kb_id'],'type':'kb_summary','category':x['category'],'reference_url':x.get('official_reference_url','')}))
    for x in json.loads((ROOT/'data/kb_articles.json').read_text()):
        content = (ROOT/'data'/x['content_file']).read_text()
        docs.append(Document(page_content=content, metadata={
            'source_id':x['kb_id'], 'title':x['title'], 'type':'kb_article',
            'category':x['category'], 'source_file':x['content_file'],
            'reference_url':x.get('official_reference_url',''),
        }))
    return docs

def load_chunks(settings=None):
    return chunk_documents(load_docs(), settings or load_settings())


def group_articles(documents):
    """Discover articles from metadata, without assuming particular source IDs."""
    articles = {}
    for doc in documents:
        if doc.metadata.get('type') == 'kb_article':
            articles.setdefault(doc.metadata['source_id'], []).append(doc)
    return articles


def collection_name(settings=None):
    return f'{NAME}_{(settings or load_settings()).profile}'


def store(settings=None):
    return Chroma(collection_name=collection_name(settings),
                  embedding_function=OpenAIEmbeddings(model='text-embedding-3-small'),
                  persist_directory=DB, collection_metadata={'hnsw:space':'cosine'})


def manifest_path(settings):
    return Path(DB) / f'{collection_name(settings)}.json'


def fingerprint(documents, settings):
    contents = {'profile':settings.profile, 'documents':[
        {'text':d.page_content, 'metadata':d.metadata} for d in documents]}
    return hashlib.sha256(json.dumps(contents, sort_keys=True).encode()).hexdigest()


def validate_index(vectors, documents, settings):
    """Reject stale indexes rather than searching different data in BM25 and Chroma."""
    path = manifest_path(settings)
    message = f'Index missing or out of date for {settings.profile}. Run python -m src.ingest with the same chunk settings.'
    if not path.exists() or json.loads(path.read_text()).get('fingerprint') != fingerprint(documents, settings):
        raise ValueError(message)
    if set(vectors.get(include=[])['ids']) != {d.metadata['chunk_id'] for d in documents}:
        raise ValueError(message)


def build_index(settings):
    documents = load_chunks(settings)
    vectors = store(settings)
    old_ids = set(vectors.get(include=[])['ids'])
    ids = [d.metadata['chunk_id'] for d in documents]
    vectors.add_documents(documents, ids=ids)
    stale = old_ids - set(ids)
    if stale:
        vectors.delete(ids=sorted(stale))
    manifest_path(settings).write_text(json.dumps({
        'fingerprint':fingerprint(documents, settings), 'records':len(documents),
        'collection':collection_name(settings),
    }, indent=2) + '\n')
    print(f'Indexed {len(documents)} records into {collection_name(settings)}')
    return documents


def main():
    parser = argparse.ArgumentParser(description='Index the shared BM25/Chroma document chunks.')
    add_chunk_arguments(parser)
    parser.add_argument('--activate', action='store_true', help='Save these settings for the app after successful indexing')
    parser.add_argument('--dry-run', action='store_true', help='Preview chunk counts without embeddings or database writes')
    args = parser.parse_args()
    settings = settings_from_args(args)
    if args.dry_run:
        documents = load_chunks(settings)
        print(f'{len(load_docs())} source records -> {len(documents)} searchable records; collection: {collection_name(settings)}')
        for source_id, article_chunks in group_articles(documents).items():
            print(f"{source_id}: {len(article_chunks)} chunk(s) — {article_chunks[0].metadata.get('title',source_id)}")
        return
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=True)
    build_index(settings)
    if args.activate:
        save_settings(settings)
        print('Settings saved. Restart Streamlit to load this index.')


if __name__=='__main__':
    main()
