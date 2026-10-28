#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RUN_ID="${1:-$(date +%Y%m%d_%H%M%S)}"
[[ "$RUN_ID" =~ ^[A-Za-z0-9_-]+$ ]] || exit 2
BASE="/user/$(id -un)/lab2_edge_${RUN_ID}"
if hdfs dfs -test -e "$BASE"; then echo 'Use a fresh run id' >&2; exit 2; fi
mkdir -p build/fixtures
printf 'Data data DATA, hadoop! the and 123\nindex-index\n' > build/fixtures/a.txt
printf 'Hadoop; search data. THE\n' > build/fixtures/b.txt
: > build/fixtures/empty.txt
printf 'the THE and a an\n' > build/fixtures/stop.txt
hdfs dfs -mkdir -p "$BASE/input"
hdfs dfs -put build/fixtures/*.txt "$BASE/input/"
hdfs dfs -put stopwords.txt "$BASE/stopwords.txt"
hadoop jar build/inverted-index.jar "$BASE/input" "$BASE/output" "$BASE/stopwords.txt"
hdfs dfs -cat "$BASE/output/part-r-00000" > build/edge-actual.txt
printf 'data\t<a.txt,3>;<b.txt,1>;<total,4>.\nhadoop\t<a.txt,1>;<b.txt,1>;<total,2>.\nindex\t<a.txt,2>;<total,2>.\nsearch\t<b.txt,1>;<total,1>.\n' > build/edge-expected.txt
diff -u build/edge-expected.txt build/edge-actual.txt
echo 'PASS: real Hadoop boundary job'
