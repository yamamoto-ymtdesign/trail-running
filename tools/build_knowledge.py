"""Build the knowledge document the app's question box reads.

Concatenates the project docs into one text and writes it as JSON for the
`knowledge/main` document of the log app:

    python3 tools/build_knowledge.py /path/to/knowledge.json

Then upload it with the ArtifactData tool (set, collection "knowledge",
doc_id "main", file_path = that JSON). Re-run after any doc changes.
"""
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ["docs/session-notes.md", "docs/athlete.md", "docs/race.md", "plan/training-plan.md"]


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "knowledge.json"
    parts = [f"===== {name} =====\n{(ROOT / name).read_text(encoding='utf-8').strip()}" for name in SOURCES]
    body = "\n\n".join(parts)
    doc = {"body": body, "sources": SOURCES, "updatedAt": datetime.date.today().isoformat()}
    out.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    print(f"{out}: {len(body)} chars, {len(body.encode('utf-8'))} bytes")


if __name__ == "__main__":
    main()
