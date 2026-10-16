# IT Support RAG Assistant

## Setup (Mac/Linux)
1. Install Python 3.11 or 3.12.
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `python -m pip install -r requirements.txt`
5. `cp .env.example .env` and replace the API key value with your OpenAI API key. Never commit `.env`.
6. `python -m src.ingest` (makes embeddings and persists Chroma index; API usage costs money).
7. `streamlit run app.py`

Windows PowerShell activation: `.venv\\Scripts\\Activate.ps1`. Copy the .env file manually or use `Copy-Item .env.example .env`.

## Project structure
- `data/incidents.json`: 40 synthetic resolved incidents
- `data/knowledge_base.json`: 5 synthetic KB summaries with official source links; **not** copies of official articles
- `data/kb_articles.json`: metadata for two longer synthetic articles
- `data/kb_articles/`: original Wi-Fi and VPN training articles with background references
- `config/retrieval.json`: active chunk settings shared by ingestion and search
- `src/chunking.py`: paragraph-aware character windows with overlap
- `src/inspect_chunks.py`: inspect article chunks without API calls
- `src/ingest.py`: LangChain Documents and Chroma index
- `src/retrieval.py`: semantic distance, BM25, hybrid RRF
- `src/assistant.py`: system prompt, structured LLM decision, citation ID check
- `app.py`: Streamlit chat UI with session history and source details
- `.streamlit/config.toml`: dark theme
- `assets/support-banner.svg`: local header illustration
- `prompts/system_prompt.txt`: grounding, clarification and escalation rules

## Chunking experiments

The default profile splits the two long articles into chunks of at most 1,000 characters, including a repeated article-title header. Adjacent article-text windows target 150 overlapping characters. Overlap starts move back to a word boundary, so actual overlap may be slightly larger. Paragraph and word boundaries are preferred at chunk ends. An unbroken token longer than a window still requires a hard split to respect the size limit and make progress. The 40 incidents and five short KB summaries stay intact.

Each chunk has a unique citation ID such as `KB-006::chunk-001`, while metadata keeps its parent article ID, title, part number and original character offsets. BM25 and Chroma use identical chunks. Citations open the actual retrieved passage, with background-reference links inside the source popup. Enable **Show retrieval details** to compare methods and expand full chunks; it is off by default and toggling it does not rerun retrieval. Chat answers always use hybrid retrieval; there is no end-user method selector. Each submitted message runs semantic search and BM25 once, then fuses their candidates. The comparison tabs are diagnostic views and do not change the answer.

Preview without API calls or database writes:

```bash
python -m src.ingest --dry-run
```

List all articles discovered from the dataset, then inspect any listed ID:

```bash
python -m src.inspect_chunks
python -m src.inspect_chunks --source-id ARTICLE_ID
python -m src.inspect_chunks --source-id ARTICLE_ID --show-text --limit 2
```

Replace `ARTICLE_ID` with an ID printed by the first command. Omit `--limit` to inspect every chunk, or use `--chunk-id` to select one exact chunk. Output includes chunk lengths, original source ranges and overlap between displayed neighbors. The inspector accepts the same `--chunk-size`, `--chunk-overlap` and `--no-chunking` options, and never modifies the index or calls OpenAI. It shows what the current local sources and chosen settings produce; re-ingest if you changed either before searching the app.

Build alternative chunk profiles using the same articles:

```bash
python -m src.ingest --no-chunking

python -m src.ingest --chunk-size 600 --chunk-overlap 100

python -m src.ingest --chunk-size 1000 --chunk-overlap 150
```

Each profile has its own Chroma collection. The original `it_support_v1` collection is preserved. Re-ingestion updates the chosen profile and removes obsolete chunks from that profile. Index validation asks you to re-ingest if the corpus or settings do not match the stored index.

CLI overrides build a profile without changing the app's settings. To switch the app after a successful build, use:

```bash
python -m src.ingest --chunk-size 600 --chunk-overlap 100 --activate
```

Restart Streamlit and start a new conversation after switching. To return to the default, build with `--chunk-size 1000 --chunk-overlap 150 --activate`. No `.env` changes are needed. Building indexes and running semantic retrieval use the OpenAI API.

## Hybrid retrieval

BM25 filters common conversational words while preserving negations, error codes and record IDs. Hybrid combines up to 15 candidates from each method with equal-weight reciprocal rank fusion (constant 60). The final five results contain at most two chunks from each parent article, leaving room for other records. Explicitly requested incident, article or chunk IDs are matched against metadata and prioritized; an unknown ID is never replaced by a partial ID match. A known article ID alone does not establish which passage answers a question, so the assistant still checks the retrieved evidence. Citation validation, clarification and human-escalation rules remain in place.

These simple settings are named constants at the top of `src/retrieval.py`. They affect ranking only; no re-ingestion is needed. Restart Streamlit and start a new conversation to use the updated retriever.

## Evaluation dashboard

Open **Evaluation** in the sidebar to compare semantic, BM25 and hybrid retrieval against the current index. Choose the main benchmark (21 answerable questions) or the held-out benchmark (10 questions), then click **Run evaluation**. Each run performs fresh searches using OpenAI embeddings and stores results only in the browser session. Changing filters or inspecting another method does not rerun searches. No saved result reports are loaded; an optional download exports the completed session result.

The method comparison table shows Hit@5 (an expected parent source appears in the top five chunks) and MRR@5 (higher scores reward earlier expected sources). The question results table shows the expected sources, ranked retrieved chunk IDs and hit or miss outcome. These metrics measure retrieval, not final-answer correctness; expected-source labels are candidate annotations, and a parent-article hit does not prove passage relevance.

Benchmark inputs live in `evals/eval_questions.csv`, `evals/kb_questions.csv` and `evals/hybrid_holdout.csv`. The page is implemented in `pages/1_Evaluation.py`; fresh evaluation and scoring are handled by `src/session_evaluation.py`. Tests, generated reports and local development utilities remain excluded from Git. Rebuild the index after changing the corpus or chunk settings before evaluating it.
