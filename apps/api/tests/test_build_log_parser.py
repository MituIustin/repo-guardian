import zipfile
from io import BytesIO

from app.build_logs.parser import extract_error_excerpt


def _archive(name: str, content: str) -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as bundle:
        bundle.writestr(name, content)
    return output.getvalue()


def test_extracts_error_context_and_redacts_secrets() -> None:
    archive = _archive(
        "build/4_test.txt",
        "setup\nTOKEN=github_pat_abcdefghijklmnopqrstuvwxyz\nrunning tests\n"
        "ERROR: expected 2 but received 3\ncleanup\n",
    )

    excerpt = extract_error_excerpt(archive)

    assert excerpt is not None
    assert excerpt.source_file == "build/4_test.txt"
    assert "ERROR: expected 2 but received 3" in excerpt.content
    assert "github_pat_abcdefghijklmnopqrstuvwxyz" not in excerpt.content
    assert "[REDACTED]" in excerpt.content


def test_returns_none_when_log_has_no_recognizable_error() -> None:
    assert extract_error_excerpt(_archive("build.txt", "everything is fine")) is None
