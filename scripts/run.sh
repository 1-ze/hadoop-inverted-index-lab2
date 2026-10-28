#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# A fresh HDFS directory per execution; existing experiments are never removed.
RUN_ID="${1:-$(date +%Y%m%d_%H%M%S)}"
[[ "$RUN_ID" =~ ^[A-Za-z0-9_-]+$ ]] || { echo 'Invalid run id' >&2; exit 2; }
BASE="/user/$(id -un)/lab2_${RUN_ID}"
mkdir -p results
if hdfs dfs -test -e "$BASE"; then
  echo "HDFS path already exists: $BASE; choose a new run id" >&2; exit 2
fi
hdfs dfs -mkdir -p "$BASE/input"
hdfs dfs -put data/*.txt "$BASE/input/"
hdfs dfs -put stopwords.txt "$BASE/stopwords.txt"
hdfs dfs -ls "$BASE/input" | tee results/hdfs-input.txt
printf 'HDFS_BASE=%s\n' "$BASE" | tee results/run-info.txt
hadoop jar build/inverted-index.jar "$BASE/input" "$BASE/output" "$BASE/stopwords.txt" 2>&1 | tee results/hadoop-job.log
hdfs dfs -cat "$BASE/output/part-r-00000" > results/inverted-index.txt
hdfs dfs -ls "$BASE/output" | tee results/hdfs-output.txt
python3 scripts/validate.py
