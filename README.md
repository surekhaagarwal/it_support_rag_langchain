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
