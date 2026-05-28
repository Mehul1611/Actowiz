from pathlib import Path
from app.utils.pdf_parser import extract_pdf_text


TEXT_EXTENSIONS = {".txt", ".md", ".py", ".js", ".java"}


def load_file_content(file_path, file_type):
    path = Path(file_path)
    ext = file_type if file_type.startswith(".") else f".{file_type}"

    if ext == ".pdf":
        return extract_pdf_text(str(path))

    if ext in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="ignore")

    raise ValueError(f"unsupported file type: {ext}")
