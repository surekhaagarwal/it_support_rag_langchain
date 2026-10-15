from typing import Literal
from pydantic import BaseModel,Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.ingest import ROOT
from src.retrieval import Search

class Answer(BaseModel):
    status:Literal['RESOLVED_GUIDANCE','NEEDS_CLARIFICATION','ESCALATE_NO_EVIDENCE','ESCALATE_INSUFFICIENT_EVIDENCE','ESCALATE_HIGH_RISK']
    issue_summary:str=''
    suggested_resolution:list[str]=Field(default_factory=list)
    sources:list[str]=Field(default_factory=list)
    escalation_reason:str|None=None
    clarifying_question:str|None=None

class Assistant:
    def __init__(self):
        self.search=Search()
        self.llm=ChatOpenAI(model='gpt-4.1-mini',temperature=0).with_structured_output(Answer)
        self.prompt=ChatPromptTemplate.from_messages([('system',(ROOT/'prompts/system_prompt.txt').read_text()),('human','Issue: {question}\n\nEvidence:\n{evidence}\n\nReturn a structured decision.')])
    def ask(self,q,mode='hybrid'):
        if not q.strip():return Answer(status='NEEDS_CLARIFICATION',clarifying_question='What error or symptom are you seeing?'),[]
        found=self.search.query(q,mode,k=5)
        evidence='\n\n'.join(f"SOURCE_ID: {x['id']}\n{x['doc'].page_content}" for x in found) or '(no retrieved records)'
        result=(self.prompt|self.llm).invoke({'question':q,'evidence':evidence})
        if not set(result.sources).issubset({x['id'] for x in found}):
            return Answer(status='ESCALATE_INSUFFICIENT_EVIDENCE',escalation_reason='Invalid source citation.'),found
        if result.status!='RESOLVED_GUIDANCE': 
            result.sources = []
            result.suggested_resolution=[]
        if result.status=='RESOLVED_GUIDANCE' and (not result.sources or not result.suggested_resolution):
            return Answer(status='ESCALATE_INSUFFICIENT_EVIDENCE',escalation_reason='Insufficient cited guidance.'),found
        return result,found
