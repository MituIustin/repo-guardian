import re
import zipfile
from dataclasses import dataclass
from io import BytesIO

MAX_ARCHIVE_BYTES = 25 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_EXCERPT_LINES = 120
ERROR_PATTERN = re.compile(
    r"(?i)(##\[error\]|\berror\b|\bfailed\b|\bfatal\b|exception|traceback|npm err!)"
)
SECRET_PATTERNS = (
    re.compile(r"(?i)(authorization:\s*(?:bearer|token)\s+)\S+"),
    re.compile(r"(?i)((?:password|secret|token|api[_-]?key)\s*[=:]\s*)\S+"),
    re.compile(r"\b(?:gh[opsu]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
)


class LogArchiveError(ValueError):
    """Raised when a log archive is invalid or exceeds safety limits."""


@dataclass(frozen=True)
class ExtractedLogExcerpt:
    source_file: str
    start_line: int
    end_line: int
    content: str


def extract_error_excerpt(archive: bytes) -> ExtractedLogExcerpt | None:
    if not archive or len(archive) > MAX_ARCHIVE_BYTES:
        raise LogArchiveError("The workflow log archive is empty or too large")
    try:
        with zipfile.ZipFile(BytesIO(archive)) as bundle:
            files = [item for item in bundle.infolist() if not item.is_dir()]
            if sum(item.file_size for item in files) > MAX_UNCOMPRESSED_BYTES:
                raise LogArchiveError("The workflow log archive expands beyond the limit")
            best: ExtractedLogExcerpt | None = None
            for item in files:
                if item.file_size > MAX_FILE_BYTES:
                    continue
                lines = bundle.read(item).decode("utf-8", errors="replace").splitlines()
                matches = [index for index, line in enumerate(lines) if ERROR_PATTERN.search(line)]
                if not matches:
                    continue
                end = min(len(lines), matches[-1] + 4)
                start = max(0, end - MAX_EXCERPT_LINES)
                ordered = list(range(start, end))
                content = "\n".join(_redact(lines[index])[:2000] for index in ordered)
                candidate = ExtractedLogExcerpt(
                    source_file=item.filename[-1024:],
                    start_line=ordered[0] + 1,
                    end_line=ordered[-1] + 1,
                    content=content,
                )
                if best is None or len(candidate.content) > len(best.content):
                    best = candidate
            return best
    except (zipfile.BadZipFile, RuntimeError) as error:
        raise LogArchiveError("The workflow log archive is invalid") from error


def _redact(line: str) -> str:
    redacted = line
    for pattern in SECRET_PATTERNS:
        replacement = r"\1[REDACTED]" if pattern.groups else "[REDACTED]"
        redacted = pattern.sub(replacement, redacted)
    return redacted
