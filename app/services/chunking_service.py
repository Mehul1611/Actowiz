import re
from app.core.config import settings
from app.utils.tokenizer import split_text_by_tokens


CODE_EXTENSIONS = {".py", ".js", ".java"}


def chunk_text(text, file_type=".txt"):
    ext = file_type if file_type.startswith(".") else f".{file_type}"
    if ext in CODE_EXTENSIONS:
        return chunk_code_blocks(text)
    return chunk_plain_text(text)


def chunk_plain_text(text):
    pieces = split_text_by_tokens(text, settings.chunk_size, settings.chunk_overlap)
    return [{"index": i, "content": p, "metadata": {"kind": "text"}} for i, p in enumerate(pieces)]


def chunk_code_blocks(text):
    pattern = re.compile(r"(?=^(?:class |def |function |public class ))", re.MULTILINE)
    blocks = [b.strip() for b in pattern.split(text) if b.strip()]

    if not blocks:
        return chunk_plain_text(text)

    chunks = []
    idx = 0
    for block in blocks:
        if count_words(block) > settings.chunk_size:
            for piece in split_text_by_tokens(block, settings.chunk_size, settings.chunk_overlap):
                chunks.append({
                    "index": idx,
                    "content": piece,
                    "metadata": {"kind": "code", "split": "token"},
                })
                idx += 1
        else:
            chunks.append({
                "index": idx,
                "content": block,
                "metadata": {"kind": "code", "split": "symbol"},
            })
            idx += 1
    return chunks


def count_words(text):
    return len(text.split())
