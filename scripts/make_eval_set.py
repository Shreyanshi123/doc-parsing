"""Build eval/ from the synthetic samples: each document + a hand-written ground truth (<file>.truth.md).

    python scripts/make_eval_set.py

For YOUR real documents: drop the file in eval/ and write <file>.truth.md next to it
(the correct content as Markdown: '#' headings, '|' tables, plain paragraphs).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from make_samples import PARA, TABLE, TITLE  # noqa: E402

SAMPLES, EVAL = ROOT / "samples", ROOT / "eval"


def md_table(rows):
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


TRUTH = {
    "digital.pdf": f"# {TITLE}\n\n{PARA}\n\n{md_table(TABLE)}\n",
    "scanned.pdf": f"# {TITLE}\n\n{PARA}\n",
    "scan.png": f"# {TITLE}\n\n{PARA}\n",
    "mixed.pdf": f"# {TITLE}\n\n{PARA}\n\n{md_table(TABLE)}\n\n# {TITLE}\n\n{PARA}\n",
    "report.docx": (f"# {TITLE}\n\n## Summary\n\n{PARA}\n\n- North region led growth\n- West region improved margins\n\n"
                    f"{md_table(TABLE)}\n"),
    "deck.pptx": f"# {TITLE}\n\n- Revenue up 12%\n- Customer satisfaction improved\n\nMention the West region.\n",
    "sales.xlsx": f"{md_table(TABLE)}\n\n{md_table([['Comment', 'Prepared by finance']])}\n",
    "sales.csv": f"{md_table(TABLE)}\n",
}

if __name__ == "__main__":
    EVAL.mkdir(exist_ok=True)
    for name, truth in TRUTH.items():
        src = SAMPLES / name
        if not src.exists():
            print(f"missing sample {name} (run scripts/make_samples.py first)")
            continue
        shutil.copy(src, EVAL / name)
        (EVAL / f"{name}.truth.md").write_text(truth, encoding="utf-8")
        print("eval/" + name)
