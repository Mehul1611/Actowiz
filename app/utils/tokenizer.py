def count_tokens(text):
    return len(text.split())


def split_text_by_tokens(text, chunk_size, overlap):
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        piece = " ".join(words[start:end])
        chunks.append(piece)
        if end >= len(words):
            break
        start = max(0, end - overlap)
    return chunks
