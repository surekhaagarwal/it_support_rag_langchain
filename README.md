# IT Support Resolution RAG — one-week starter

## Setup (Mac/Linux)
1. Install Python 3.11 or 3.12.
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `python -m pip install -r requirements.txt`
5. `cp .env.example .env` and replace the API key value with your OpenAI API key. Never commit `.env`.
6. `python -m src.ingest` (makes embeddings and persists Chroma index; API usage costs money).
7. `streamlit run app.py`
8. `python -m src.evaluate` to produce `evals/retrieval_results.json`.

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`. Copy the .env file manually or use `Copy-Item .env.example .env`.

## Project structure
- `data/incidents.json`: 40 synthetic resolved incidents
- `data/knowledge_base.json`: 5 synthetic KB summaries with official source links; **not** copies of official articles
- `src/ingest.py`: LangChain Documents and Chroma index
- `src/retrieval.py`: semantic distance, BM25, hybrid RRF
- `src/assistant.py`: system prompt, structured LLM decision, citation ID check
- `src/evaluate.py`: custom Hit@5 and MRR@5
- `evals/eval_questions.csv`: 20 candidate eval questions
- `app.py`: Streamlit UI

## Seven-day learning plan
Day 1: Review data and candidate gold labels; run setup.
Day 2: Study JSON -> Document conversion and run ingestion.
Day 3: Inspect semantic results and raw distances.
Day 4: Compare BM25 and RRF.
Day 5: Inspect system prompt, citations and escalation.
Day 6: Run custom retrieval evals; manually score answer quality and escalation.
Day 7: Demo UI, document failure cases and lessons learned.

## Limitations / safety
- This is a learning prototype, not a production helpdesk tool. It does not create real support tickets or contact humans.
- No similarity threshold is treated as proof of relevance. Chroma is configured with cosine distance; semantic similarity is shown as `1 - distance`. This is not a probability of answer correctness. If you created an index with a different distance metric, delete `chroma_db/` and reindex.
- An LLM-based evidence check can make mistakes; citation ID verification does not guarantee claim-level faithfulness.
- The 20 labels are candidates, not independently verified gold standards. Review them before reporting accuracy.
- Synthetic KB summaries link to public Microsoft pages but do not represent their complete text.
- Keep credentials and personal data out of inputs and source records.
