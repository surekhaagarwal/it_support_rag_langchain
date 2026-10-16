"""Inspect prepared article chunks locally, without API calls or database writes."""
import argparse
from src.chunking import add_chunk_arguments, settings_from_args
from src.ingest import group_articles, load_chunks


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    add_chunk_arguments(parser)
    parser.add_argument('--source-id', help='An article ID from the summary; omit to list all articles')
    parser.add_argument('--chunk-id', help='Inspect just one exact chunk ID')
    parser.add_argument('--show-text', action='store_true', help='Print complete chunk text, not just its boundaries')
    parser.add_argument('--limit', type=int, help='Maximum chunks to show; by default show every matching chunk')
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit <= 0:
        parser.error('--limit must be positive')
    settings = settings_from_args(args)
    articles = group_articles(load_chunks(settings))
    if args.source_id and args.source_id not in articles:
        parser.error('Unknown article ID. Available IDs: ' + ', '.join(articles))
    print(f'Profile: {settings.profile} (prepared from local source files)')
    if not args.source_id and not args.chunk_id and not args.show_text:
        for source_id, chunks in articles.items():
            print(f"{source_id}: {len(chunks)} chunk(s) — {chunks[0].metadata.get('title',source_id)}")
        return
    chunks = articles[args.source_id] if args.source_id else [doc for group in articles.values() for doc in group]
    if args.chunk_id:
        chunks = [doc for doc in chunks if doc.metadata['chunk_id'] == args.chunk_id]
        if not chunks:
            parser.error('No matching article chunk. Check the source ID, chunk ID and selected profile.')
    shown = chunks if args.limit is None else chunks[:args.limit]
    print(f'Showing {len(shown)} of {len(chunks)} matching chunks. Source end offsets are exclusive.')
    previous_ends = {}
    for doc in shown:
        metadata = doc.metadata
        source_id = metadata['source_id']
        start, end = metadata['start_char'], metadata['end_char']
        previous_end = previous_ends.get(source_id)
        overlap = max(0, previous_end - start) if previous_end is not None else None
        print(f"\n{metadata['chunk_id']} | Article: {source_id} | Part {metadata['chunk_index'] + 1}/{metadata['chunk_count']}")
        print(f"Length: {len(doc.page_content)} characters | Source range: {start}:{end}")
        if overlap is not None:
            print(f'Overlap with previous displayed chunk: {overlap} characters')
        if args.show_text:
            print(doc.page_content)
        previous_ends[source_id] = end


if __name__ == '__main__':
    main()
