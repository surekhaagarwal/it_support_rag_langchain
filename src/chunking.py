"""Small character-based splitter; no extra packages required."""
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config/retrieval.json'


@dataclass(frozen=True)
class ChunkSettings:
    enabled: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 150

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError('enabled must be true or false')
        if type(self.chunk_size) is not int or self.chunk_size <= 0:
            raise ValueError('chunk_size must be a positive integer')
        if type(self.chunk_overlap) is not int or not 0 <= self.chunk_overlap < self.chunk_size:
            raise ValueError('chunk_overlap must be between 0 and chunk_size - 1')

    @property
    def profile(self):
        return f'c{self.chunk_size}_o{self.chunk_overlap}' if self.enabled else 'whole'


def load_settings():
    return ChunkSettings(**json.loads(CONFIG_PATH.read_text()))


def save_settings(settings):
    CONFIG_PATH.write_text(json.dumps(asdict(settings), indent=2) + '\n')


def add_chunk_arguments(parser):
    parser.add_argument('--chunk-size', type=int, help='Maximum characters per article chunk, including its title header')
    parser.add_argument('--chunk-overlap', type=int, help='Target overlapping article characters; word alignment may increase it slightly')
    parser.add_argument('--no-chunking', action='store_true', help='Keep each article whole for a baseline comparison')


def settings_from_args(args):
    settings = load_settings()
    updates = {}
    if args.no_chunking:
        updates['enabled'] = False
    elif args.chunk_size is not None or args.chunk_overlap is not None:
        updates['enabled'] = True
    for name in ('chunk_size', 'chunk_overlap'):
        value = getattr(args, name)
        if value is not None:
            updates[name] = value
    return replace(settings, **updates)


def text_windows(text, size, overlap):
    """Prefer readable ends and word-aligned overlap starts, within the size limit."""
    if size <= 0 or not 0 <= overlap < size:
        raise ValueError('Text window size must exceed overlap')
    windows = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            lower = max(start + size // 2, start + overlap + 1)
            boundary = text.rfind('\n\n', lower, end)
            if boundary != -1:
                end = boundary + 2
            else:
                boundary = text.rfind(' ', lower, end)
                if boundary != -1:
                    end = boundary + 1
        windows.append((start, end))
        if end == len(text):
            break
        next_start = end - overlap
        if overlap:
            # Move back to the beginning of the overlapping word, never forwards
            # past text that has not been covered. Preserve progress for a token
            # longer than the whole window, where a word boundary is impossible.
            aligned_start = next_start
            while aligned_start > start and not text[aligned_start - 1].isspace():
                aligned_start -= 1
            if aligned_start > start:
                next_start = aligned_start
        start = next_start
    return windows


def chunk_documents(documents, settings):
    from langchain_core.documents import Document

    chunks = []
    for doc in documents:
        source_id = doc.metadata['source_id']
        metadata = dict(doc.metadata)
        # Short records retain their text and citation IDs.
        if not settings.enabled or doc.metadata['type'] != 'kb_article' or len(doc.page_content) <= settings.chunk_size:
            metadata.update(chunk_id=source_id, chunk_index=0, chunk_count=1,
                            start_char=0, end_char=len(doc.page_content))
            chunks.append(Document(page_content=doc.page_content, metadata=metadata))
            continue
        header = f"kb_id: {source_id}\ntitle: {metadata['title']}\n\n"
        body_size = settings.chunk_size - len(header)
        if body_size <= settings.chunk_overlap:
            raise ValueError(f'Chunk size must leave more than {settings.chunk_overlap} characters after the title header for {source_id}')
        windows = text_windows(doc.page_content, body_size, settings.chunk_overlap)
        for index, (start, end) in enumerate(windows):
            chunk_metadata = dict(metadata, chunk_id=f'{source_id}::chunk-{index + 1:03d}',
                                  chunk_index=index, chunk_count=len(windows), start_char=start, end_char=end)
            chunks.append(Document(page_content=header + doc.page_content[start:end], metadata=chunk_metadata))
    return chunks
