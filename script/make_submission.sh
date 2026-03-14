#!/bin/bash
# Build a clean Gradescope submission zip.
# Includes only the files the autograder needs, avoiding the src/utils/
# package that shadows the autograder's own utils.py.

set -euo pipefail
cd "$(dirname "$0")/.."

OUT="submission.zip"
rm -f "$OUT"

zip -r "$OUT" \
    results/t5_ft_test.sql \
    results/t5_scr_test.sql \
    results/llm_test.sql \
    records/t5_ft_test.pkl \
    records/t5_scr_test.pkl \
    records/llm_test.pkl \
    report/report.pdf \
    -x '*.DS_Store' '__MACOSX/*'

echo ""
echo "Created $OUT ($(du -h "$OUT" | cut -f1))"
echo "Contents:"
unzip -l "$OUT"
