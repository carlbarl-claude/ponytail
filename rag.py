"""Retrieval-augmented grounding for the AP tutor bot.

Indexes a per-subject knowledge library (rubric summaries, scored samples, and any
PDFs/notes the student uploads) and retrieves the most relevant chunks for a given
question. Uses lightweight BM25 keyword search — no embedding API, no extra keys,
deterministic, and plenty good at this scale. Swap in embeddings later if you want
semantic matching.

Library layout (per subject key, e.g. "euro", "seminar"):
    knowledge/ap_<subject>/rubrics.md      -> tagged as "rubric"
    knowledge/ap_<subject>/samples.md      -> tagged as "scored sample"
    knowledge/ap_<subject>/uploads/*.pdf   -> tagged as "your upload"
    knowledge/ap_<subject>/uploads/*.txt|.md
"""

import io
import os
import re
import glob

from rank_bm25 import BM25Okapi

# Maps the bot's subject keys to their knowledge subdirectory name.
SUBJECT_DIRS = {
    "euro": "ap_euro",
    "seminar": "ap_seminar",
}

KNOWLEDGE_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge")

# Small stopword set so common words don't dominate BM25 scoring.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "it", "this", "that", "as", "at", "by",
    "how", "do", "i", "my", "me", "you", "your", "can", "what", "which",
}

_ALLOWED_UPLOAD_EXTS = {".pdf", ".txt", ".md"}


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS]


def _chunk_markdown(text: str) -> list[tuple[str, str]]:
    """Split markdown into (title, body) chunks at each `##`/`###` heading."""
    chunks: list[tuple[str, str]] = []
    current_title = "Overview"
    current_lines: list[str] = []

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append((current_title, body))

    for line in text.splitlines():
        m = re.match(r"^#{2,3}\s+(.*)", line)
        if m:
            flush()
            current_title = m.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()
    return chunks


def _chunk_plain(text: str, size: int = 1100) -> list[tuple[str, str]]:
    """Split plain/PDF text into ~size-char chunks, breaking on blank lines."""
    chunks: list[tuple[str, str]] = []
    paras = re.split(r"\n\s*\n", text)
    buf = ""
    part = 1
    for para in paras:
        para = para.strip()
        if not para:
            continue
        if len(buf) + len(para) + 2 > size and buf:
            chunks.append((f"section {part}", buf.strip()))
            part += 1
            buf = ""
        buf += para + "\n\n"
    if buf.strip():
        chunks.append((f"section {part}", buf.strip()))
    return chunks


def _extract_pdf_text(data: bytes) -> str:
    from pypdf import PdfReader  # imported lazily so the bot starts even without a PDF

    reader = PdfReader(io.BytesIO(data))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def _source_type_for(path: str) -> str:
    name = os.path.basename(path).lower()
    if "uploads" in path.replace("\\", "/").split("/"):
        return "your upload"
    if name.startswith("rubric"):
        return "rubric"
    if name.startswith("sample"):
        return "scored sample"
    return "note"


class SubjectIndex:
    """A BM25 index over one subject's knowledge library."""

    def __init__(self, subject_key: str):
        self.subject_key = subject_key
        self.dir = os.path.join(KNOWLEDGE_ROOT, SUBJECT_DIRS[subject_key])
        self.chunks: list[dict] = []  # each: {title, body, source, doc}
        self.bm25: BM25Okapi | None = None
        self.rebuild()

    def _load_file(self, path: str) -> None:
        source = _source_type_for(path)
        doc_name = os.path.splitext(os.path.basename(path))[0]
        try:
            if path.lower().endswith(".pdf"):
                with open(path, "rb") as f:
                    text = _extract_pdf_text(f.read())
                pieces = _chunk_plain(text)
            else:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                pieces = _chunk_markdown(text) if path.lower().endswith(".md") else _chunk_plain(text)
        except Exception as e:  # a corrupt PDF shouldn't take down the whole index
            print(f"[rag] skipped {path}: {e}")
            return

        for title, body in pieces:
            self.chunks.append(
                {"title": title, "body": body, "source": source, "doc": doc_name}
            )

    def rebuild(self) -> None:
        """(Re)scan the subject directory and rebuild the BM25 index."""
        self.chunks = []
        patterns = ["*.md", "*.txt", os.path.join("uploads", "*.pdf"),
                    os.path.join("uploads", "*.txt"), os.path.join("uploads", "*.md")]
        seen = set()
        for pat in patterns:
            for path in sorted(glob.glob(os.path.join(self.dir, pat))):
                if path in seen:
                    continue
                seen.add(path)
                self._load_file(path)

        if self.chunks:
            tokenized = [_tokenize(c["title"] + " " + c["body"]) for c in self.chunks]
            self.bm25 = BM25Okapi(tokenized)
        else:
            self.bm25 = None

    def retrieve(self, query: str, k: int = 4) -> list[dict]:
        if not self.bm25 or not self.chunks:
            return []
        tokens = _tokenize(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [self.chunks[i] for i in ranked[:k] if scores[i] > 0]


# --- Module-level manager --------------------------------------------------

_indexes: dict[str, SubjectIndex] = {}


def get_index(subject_key: str) -> SubjectIndex:
    if subject_key not in _indexes:
        _indexes[subject_key] = SubjectIndex(subject_key)
    return _indexes[subject_key]


def reindex(subject_key: str) -> int:
    """Rebuild a subject's index; returns the number of chunks now indexed."""
    idx = get_index(subject_key)
    idx.rebuild()
    return len(idx.chunks)


def build_context(subject_key: str, query: str, k: int = 4) -> str:
    """Return a formatted CONTEXT block for the system prompt, or '' if nothing hits."""
    hits = get_index(subject_key).retrieve(query, k=k)
    if not hits:
        return ""
    parts = ["=== STUDY LIBRARY CONTEXT (retrieved for this question) ==="]
    for h in hits:
        parts.append(f"[{h['source']} · {h['doc']} · \"{h['title']}\"]\n{h['body']}")
    parts.append("=== END CONTEXT ===")
    return "\n\n".join(parts)


def library_summary(subject_key: str) -> str:
    """Human-readable summary of what's currently indexed for a subject."""
    idx = get_index(subject_key)
    if not idx.chunks:
        return "The library is empty for this subject."
    by_source: dict[str, set] = {}
    for c in idx.chunks:
        by_source.setdefault(c["source"], set()).add(c["doc"])
    lines = [f"{len(idx.chunks)} indexed sections across:"]
    for source, docs in sorted(by_source.items()):
        lines.append(f"• {source}: {', '.join(sorted(docs))}")
    return "\n".join(lines)


def ingest_upload(subject_key: str, filename: str, data: bytes) -> tuple[bool, str]:
    """Save an uploaded file into the subject's uploads/ dir and reindex."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _ALLOWED_UPLOAD_EXTS:
        return False, f"I can only ingest PDF, TXT, or MD files (got '{ext or 'no extension'}')."

    # Sanitize the filename to avoid path traversal.
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(filename)) or f"upload{ext}"
    uploads_dir = os.path.join(get_index(subject_key).dir, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    dest = os.path.join(uploads_dir, safe)
    try:
        with open(dest, "wb") as f:
            f.write(data)
    except OSError as e:
        return False, f"Couldn't save the file: {e}"

    total = reindex(subject_key)
    return True, f"Added **{safe}** to the library. It's now searchable ({total} sections indexed)."
