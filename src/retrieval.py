import re
from collections import defaultdict
from rank_bm25 import BM25Okapi
from src.ingest import load_docs,store

def tokens(s):
    return re.findall(r'[a-z0-9]+(?:[-_.][a-z0-9]+)*',s.lower())

class Search:
    def __init__(self):
        self.docs=load_docs()
        self.bm=BM25Okapi([tokens(d.page_content) for d in self.docs])
        self.vectors=store()
    def semantic(self,q,k=5):
        # The index is configured with cosine distance. Similarity = 1 - distance.
        return [{'id':d.metadata['source_id'],'doc':d,'distance':float(distance),'similarity':1-float(distance)} for d,distance in self.vectors.similarity_search_with_score(q,k=k)]
    def keyword(self,q,k=5):
        scores=self.bm.get_scores(tokens(q))
        ranks=sorted(enumerate(scores),key=lambda t:t[1],reverse=True)
        return [{'id':self.docs[i].metadata['source_id'],'doc':self.docs[i],'bm25_score':float(score)} for i,score in ranks[:k] if score>0]
    def query(self,q,mode='hybrid',k=5):
        if mode=='semantic':return self.semantic(q,k)
        if mode=='bm25':return self.keyword(q,k)
        a=self.semantic(q,min(15,len(self.docs)))
        b=self.keyword(q,min(15,len(self.docs)))
        scores=defaultdict(float); lookup={}
        for results in (a,b):
            for rank,item in enumerate(results,1):
                scores[item['id']]+=1/(60+rank)
                lookup.setdefault(item['id'],{}).update(item)
        return [dict(lookup[id],rrf_score=scores[id]) for id in sorted(scores,key=scores.get,reverse=True)[:k]]
