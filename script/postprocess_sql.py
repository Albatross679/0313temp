"""Post-process T5-decoded SQL to fix SentencePiece comma spacing artifact.

The T5 SentencePiece tokenizer collapses ' , ' (space-comma-space) to ', '
(comma-space) during batch_decode. This script restores the original spacing
to match ground truth conventions.

Usage:
    python script/postprocess_sql.py results/t5_scr_dev.sql
    python script/postprocess_sql.py results/t5_scr_dev.sql results/t5_scr_test.sql
    python script/postprocess_sql.py results/*.sql  # all files
"""

import re
import sys
from pathlib import Path


def normalize_comma_spacing(sql: str) -> str:
    """Restore ' , ' spacing from ', ' in SQL strings.

    The regex matches a comma preceded by an alphanumeric/underscore/paren
    character (optionally with whitespace) and followed by whitespace,
    replacing with ' , '.
    """
    return re.sub(r'(?<=[a-zA-Z0-9_)])\s*,\s+', ' , ', sql)


def process_file(path: Path) -> dict:
    """Normalize comma spacing in a .sql file. Returns stats."""
    lines = path.read_text().splitlines()

    changed = 0
    normalized = []
    for line in lines:
        fixed = normalize_comma_spacing(line)
        if fixed != line:
            changed += 1
        normalized.append(fixed)

    path.write_text('\n'.join(normalized) + '\n')

    return {
        'file': str(path),
        'total_lines': len(lines),
        'lines_changed': changed,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"SKIP: {path} not found")
            continue

        stats = process_file(path)
        print(f"{stats['file']}: {stats['lines_changed']}/{stats['total_lines']} lines normalized")


if __name__ == '__main__':
    main()
