"""Session-only benchmark dashboard; no saved evaluation reports are read."""
import json
import streamlit as st
from dotenv import load_dotenv

from src.chunking import load_settings
from src.ingest import ROOT, fingerprint, load_chunks
from src.session_evaluation import LABELS, METHODS, SUITES, run_benchmark

load_dotenv(ROOT / '.env')
st.set_page_config(page_title='Retrieval Evaluation', page_icon='📊', layout='wide')
st.title('Retrieval evaluation')
st.write('Run benchmark questions against the current index and compare retrieval methods.')
st.caption('Hit@5 measures whether an expected parent source appears in the first five chunks. '
           'MRR@5 rewards expected sources ranked closer to the top. These metrics do not measure answer correctness.')

suite = st.selectbox('Benchmark questions', list(SUITES), key='evaluation_suite')
if st.button('Run evaluation', type='primary', key='run_evaluation'):
    # Never leave a previous successful result looking like the new run succeeded.
    st.session_state.pop('evaluation_result', None)
    st.session_state.pop('evaluation_error', None)
    progress = st.progress(0, text='Preparing evaluation…')
    try:
        report = run_benchmark(suite, progress=lambda current, total: progress.progress(
            current / total, text=f'Evaluating question {current} of {total}'))
        st.session_state.evaluation_result = report
    except Exception:
        st.session_state.evaluation_error = (
            'Evaluation could not finish. Check the local benchmark CSV files, API connection, '
            'and index configuration. No partial results were saved. '
            'If the data or chunk settings changed, rebuild the matching index first.'
        )
    finally:
        progress.empty()

if st.session_state.get('evaluation_error'):
    st.error(st.session_state.evaluation_error)

report = st.session_state.get('evaluation_result')
if report is None:
    st.caption('Choose a benchmark and click Run evaluation to produce fresh results.')
else:
    st.caption(f"Completed {report['completed_at']} (UTC) · {report['duration_seconds']:.1f} seconds · "
               f"Chunk profile: {report['profile']}")
    if report['suite'] != suite:
        st.warning(f"Showing the last completed run: {report['suite']}. "
                   'Click Run evaluation to evaluate your new selection.')
    try:
        settings = load_settings()
        current = fingerprint(load_chunks(settings), settings)
        if current != report['fingerprint']:
            st.warning('The dataset or chunk settings changed after this run. Run evaluation again '
                       'after rebuilding the index to measure the current configuration.')
    except Exception:
        st.warning('Unable to verify the current dataset against this session result.')

    st.subheader('Method comparison')
    summary = [{'Method': LABELS[method],
                'Hit@5': report['summary'][method]['hit_rate_at_5'],
                'MRR@5': report['summary'][method]['mrr_at_5']}
               for method in METHODS]
    st.dataframe(summary, hide_index=True)

    st.subheader('Question results')
    method = st.radio('Inspect method', list(METHODS), index=2,
                      format_func=LABELS.get, horizontal=True)
    misses_only = st.checkbox('Show misses only')
    table = []
    for row in report['rows']:
        result = row['methods'][method]
        if misses_only and result['hit_at_5']:
            continue
        table.append({'Question ID': row['id'], 'Question': row['question'],
                      'Expected sources': ', '.join(row['gold']),
                      'Retrieved chunks (ranked)': ', '.join(result['retrieved_ids']),
                      'Result': 'Hit' if result['hit_at_5'] else 'Miss',
                      'Reciprocal rank': result['rr_at_5']})
    if table:
        st.dataframe(table, hide_index=True)
    else:
        st.success('No misses for this method in the completed run.')
    st.download_button('Download this session result', json.dumps(report, indent=2),
                       file_name='session_retrieval_evaluation.json', mime='application/json')
