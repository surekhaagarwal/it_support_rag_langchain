import streamlit as st
from base64 import b64encode
from inspect import signature
from urllib.parse import urlsplit
from dotenv import load_dotenv
from src.ingest import ROOT
from src.assistant import Assistant
load_dotenv(ROOT/'.env')
st.set_page_config(page_title='IT Support RAG Assistant', page_icon='🛠️', layout='wide')
# Give the evaluation dashboard explicit navigation labels. The chat
# continues below; evaluation renders its own page and stops before the chat UI.
if (ROOT / 'pages/1_Evaluation.py').exists():
    def chat_page():
        """The default chat page is rendered below the navigation."""

    page = st.navigation([
        st.Page(chat_page, title='Chat', icon='💬', default=True),
        st.Page('pages/1_Evaluation.py', title='Evaluation', icon='📊'),
    ])
    page.run()
    if page.title != 'Chat':
        st.stop()
# A local decorative SVG keeps the banner sharp without external image requests.
banner_art = b64encode((ROOT / 'assets/support-banner.svg').read_bytes()).decode('ascii')
st.markdown("""
<style>
    .block-container { max-width: 1400px; padding-top: 2.5rem; }
    h1 { font-size: 2rem; letter-spacing: -0.025em; }
    .st-key-app_header {
        background-color: #162235;
        background-image: url("data:image/svg+xml;base64,__BANNER_ART__");
        background-position: right 1.25rem center;
        background-size: 170px auto;
        background-repeat: no-repeat;
        padding: 1.5rem 205px 1.5rem 1.75rem;
        border: 1px solid #334155;
        border-top: 3px solid #60a5fa;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }
    .st-key-app_header h1 { padding: 0; margin: 0; color: #f1f5f9; }
    .banner-eyebrow {
        color: #93c5fd; font-size: 0.72rem; font-weight: 600;
        letter-spacing: 0.12em; margin: 0;
    }
    .banner-subtitle { color: #b6c4d6; font-size: 0.95rem; margin: 0; }
    @media (max-width: 1150px) {
        .st-key-app_header {
            background-image: none;
            padding: 1.5rem;
        }
    }
    @media (max-width: 767px) {
        .st-key-app_header h1 { font-size: 1.65rem; }
    }
    @media (min-width: 768px) {
        .st-key-app_header [data-testid="stHorizontalBlock"] { gap: 1rem; }
        .st-key-app_header [data-testid="stColumn"] {
            flex: 0 1 auto;
            width: max-content;
        }
        .st-key-app_header h1 { white-space: nowrap; }
    }
    .st-key-new_conversation button {
        background-color: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
        min-height: 2rem;
        padding: 0.3rem 0.7rem;
    }
    .st-key-new_conversation button p { font-size: 0.82rem; }
    .st-key-new_conversation button:hover {
        background-color: #bfdbfe;
        border-color: #93c5fd;
        color: #1e3a8a;
    }
    /* Wrapping fallback for Streamlit versions without horizontal containers. */
    [class*="st-key-citation_row_legacy_"] {
        flex-direction: row; flex-wrap: wrap; gap: 0.5rem;
    }
    [class*="st-key-citation_row_legacy_"] > [data-testid="stElementContainer"] {
        width: auto; flex: 0 1 auto; max-width: 100%;
    }
    [class*="st-key-retrieval_used_"] [data-testid="stExpander"] details {
        background-color: #14332b;
        border-color: #4d8e69;
        color: #dcfce7;
    }
    [class*="st-key-retrieval_used_"] [data-testid="stExpander"] summary {
        background-color: #1d4235;
        color: #dcfce7;
        border-radius: 0.5rem;
    }
    [data-testid="stChatMessage"] {
        background-color: var(--secondary-background-color, #1e293b);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
    }
</style>
""".replace('__BANNER_ART__', banner_art), unsafe_allow_html=True)
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.container(key="app_header"):
    st.markdown('<p class="banner-eyebrow">IT SERVICE DESK · KNOWLEDGE ASSISTANT</p>', unsafe_allow_html=True)
    title_column, action_column = st.columns([3, 1], gap="small", vertical_alignment="center")
    with title_column:
        st.title('IT Support RAG Assistant')
    with action_column:
        if st.button("Start new conversation", type="primary", key="new_conversation"):
            st.session_state.messages = []
    st.markdown('<p class="banner-subtitle">Evidence-based troubleshooting, backed by your IT knowledge base.</p>', unsafe_allow_html=True)
st.caption('This assistant does not create tickets automatically. For further assistance, contact your IT helpdesk or submit a ticket through your support portal.')
show_details = st.toggle("Show retrieval details", value=False, key="show_retrieval_details")
if show_details:
    chat_column, retrieval_column = st.columns([2, 1], gap="large")
else:
    chat_column, retrieval_column = st.container(), None
# End users always receive hybrid search; other methods are diagnostic views.
mode = 'hybrid'
@st.cache_resource(show_spinner=False)

def get_assistant():
    """Cache models and the updated hybrid retriever; keep conversation in the session."""
    return Assistant()


@st.dialog("Source details")
def show_source(source_id, doc):
    st.subheader(source_id)
    st.caption("Synthetic project record")
    if doc.metadata.get('type') == 'kb_article':
        st.caption(f"Article: {doc.metadata['source_id']} · Part {doc.metadata.get('chunk_index',0) + 1} of {doc.metadata.get('chunk_count',1)}")
        st.markdown(doc.page_content)
    else:
        # Ingestion stores short records as one field per line.
        for line in doc.page_content.splitlines():
            label, separator, value = line.partition(":")
            if separator and value.strip():
                st.markdown("**" + label.replace("_", " ").title() + "**")
                st.write(value.strip())
            elif not separator:
                st.write(line)
    url = doc.metadata.get('reference_url', '')
    parsed = urlsplit(url)
    if parsed.scheme in ('https', 'http') and parsed.netloc:
        st.link_button('Background reference', url)


def display_citations(source_ids, found, turn_key):
    records = {record["id"]: record["doc"] for record in found}
    st.write("Cited sources:")
    options = {'key': f'citation_row_{turn_key}'}
    parameters = signature(st.container).parameters
    if 'horizontal' in parameters:
        options['horizontal'] = True
        if 'wrap' in parameters:
            options['wrap'] = True
    else:
        options['key'] = f'citation_row_legacy_{turn_key}'
    with st.container(**options):
        for source_id in dict.fromkeys(source_ids):
            doc = records.get(source_id)
            if doc is None:
                continue
            if st.button(source_id + " — View source", key=f"source_{turn_key}_{source_id}"):
                show_source(source_id, doc)


def display_answer(result, found, turn_key):
    # Display issue summary
    if result.issue_summary and result.status != "NEEDS_CLARIFICATION":
        st.write(result.issue_summary)

    # Clarification required
    if result.status == "NEEDS_CLARIFICATION":
        if result.clarifying_question:
            st.write(result.clarifying_question)

    # Human escalation required
    elif result.status.startswith("ESCALATE_"):
        review_message = " Human review is recommended."
        if result.status != "ESCALATE_NO_EVIDENCE":
            review_message = " Human review is recommended; no ticket has been created."
        st.warning(
            (result.escalation_reason or
             "Insufficient evidence to provide guidance.")
            + review_message
        )

    # Evidence-backed troubleshooting guidance
    elif result.status == "RESOLVED_GUIDANCE":
        for step in result.suggested_resolution:
            st.write("• " + step)

        if result.sources:
            display_citations(result.sources, found, turn_key)


def display_retrieval(details, cited_sources=(), status=None, selected_method=None):
    st.markdown("### Retrieval comparison")
    if status == 'NEEDS_CLARIFICATION':
        st.caption("Waiting for more details before displaying retrieval results.")
        return
    if status is not None and (status != 'RESOLVED_GUIDANCE' or not cited_sources):
        st.caption("No cited troubleshooting guidance was provided for this response.")
        return
    if not details:
        st.caption("Send a message to compare the search results here.")
        return
    st.caption("Search query")
    st.write(details['query'])
    mode_label = {'semantic': 'Semantic', 'bm25': 'BM25', 'hybrid': 'Hybrid'}[details['mode']]
    st.caption(f"Answer used: {mode_label}")
    methods = ['semantic', 'bm25', 'hybrid']
    labels = {'semantic': 'Semantic', 'bm25': 'BM25', 'hybrid': 'Hybrid'}
    selected_method = selected_method or details['mode']
    tab_options = {}
    # Older supported Streamlit versions select the first tab by default.
    parameters = signature(st.tabs).parameters
    if 'default' in parameters:
        tab_options['default'] = labels[selected_method]
    else:
        methods = [selected_method] + [method for method in methods if method != selected_method]
    if 'key' in parameters:
        tab_options['key'] = f"retrieval_tabs_{selected_method}_{len(st.session_state.messages)}"
    tabs = st.tabs([labels[method] for method in methods], **tab_options)
    for tab, method in zip(tabs, methods):
        with tab:
            rows = details['results'].get(method, [])
            if not rows:
                if method != 'bm25' and details['results'].get('error'):
                    st.caption(details['results']['error'])
                else:
                    st.caption("No matching records returned.")
            for rank, row in enumerate(rows, 1):
                used = row['id'] in cited_sources
                label = f"{rank}. {row['id']}" + (" — Used in answer" if used else "")
                # A keyed wrapper scopes the green styling to cited records only.
                with st.container(key=f"retrieval_{'used' if used else 'other'}_{method}_{rank}"):
                    with st.expander(label, expanded=False):
                        if row['doc'].metadata.get('type') == 'kb_article':
                            metadata = row['doc'].metadata
                            st.caption(f"Article: {metadata['source_id']} · Part {metadata.get('chunk_index',0) + 1} of {metadata.get('chunk_count',1)}")
                        score_labels = {
                            'distance': 'Cosine distance', 'similarity': 'Similarity',
                            'bm25_score': 'BM25 score', 'rrf_score': 'RRF score',
                        }
                        scores = [f"{label}: {row[key]:.4f}" for key, label in score_labels.items()
                                  if row.get(key) is not None]
                        if row.get('exact_id_match'):
                            scores.insert(0, 'Explicitly requested source')
                        st.caption(' · '.join(scores))
                        content = row['doc'].page_content
                        st.text(content)


with chat_column:
    conversation = st.container()

with conversation:
    welcome = st.empty()
    if not st.session_state.messages:
        with welcome.container():
            st.subheader("How can I help?")
            st.write("Describe your IT issue below. Include any error message or what happens when you try.")

    for turn_key, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.write(message["content"])
            else:
                display_answer(message["result"], message["found"], turn_key)

with chat_column:
    question = st.chat_input("Describe your issue or reply here")
if question and question.strip():
    welcome.empty()
    # Save and display the user's message before waiting for the response.
    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": question})
    with conversation, st.chat_message("user"):
        st.write(question)
    try:
        # Only this browser session owns the history; the cached assistant is stateless.
        with conversation, st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                result, found, details = get_assistant().ask_with_details(question, mode, history=history)
            st.session_state.messages.append(
                {"role": "assistant", "content": result.model_dump_json(),
                 "result": result, "found": found, "retrieval": details}
            )
            display_answer(result, found, len(st.session_state.messages) - 1)
    except Exception as exc:
        with conversation:
            st.error(
                "Unable to process request. "
                "Check API key, index and dependencies. "
                + str(exc)
            )

latest_answer = next((message for message in reversed(st.session_state.messages)
                      if message['role'] == 'assistant'), None)
if show_details:
    with retrieval_column:
        details = latest_answer.get('retrieval') if latest_answer else None
        cited_sources = (latest_answer['result'].sources
                         if latest_answer and latest_answer['result'].status == 'RESOLVED_GUIDANCE' else [])
        status = latest_answer['result'].status if latest_answer else None
        display_retrieval(details, cited_sources, status, mode)
