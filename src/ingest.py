import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
ROOT = Path(__file__).resolve().parents[1]
DB = str(ROOT / 'chroma_db')
NAME = 'it_support_v1'

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
    return docs

def store():
    return Chroma(collection_name=NAME,embedding_function=OpenAIEmbeddings(model='text-embedding-3-small'),persist_directory=DB,collection_metadata={'hnsw:space':'cosine'})

if __name__=='__main__':
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env',override=True)
    docs=load_docs()
    s=store()
    s.add_documents(docs,ids=[d.metadata['source_id'] for d in docs])
    print('Indexed',len(docs),'records')
