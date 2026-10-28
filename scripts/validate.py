"""Independent standard-library oracle; compare EVERY posting and corpus total."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]

def reference(files, stopwords):
    result = defaultdict(dict)
    raw = filtered = 0
    for file in files:
        words = [w.lower() for w in re.findall(r'[A-Za-z]+', file.read_text(encoding='utf-8'), flags=re.ASCII)]
        counts = Counter(w for w in words if w not in stopwords)
        raw += len(words)
        filtered += sum(w in stopwords for w in words)
        for term, count in counts.items(): result[term][file.name] = count
    return dict(result), raw, filtered

def parse(text):
    result = {}
    for line in text.splitlines():
        term, value = line.split('\t')
        assert re.fullmatch(r'[a-z]+',term), line
        assert re.fullmatch(r'(?:<[^<>,;]+,[1-9][0-9]*>;)+<total,[1-9][0-9]*>\.',value), line
        pairs = re.findall(r'<([^<>,;]+),([0-9]+)>',value)
        names = [name for name,_ in pairs[:-1]]
        assert names == sorted(set(names)), line
        docs = {name:int(count) for name,count in pairs[:-1]}
        assert sum(docs.values()) == int(pairs[-1][1]), line
        assert term not in result, term
        result[term] = docs
    assert list(result) == sorted(result), 'Terms must be globally sorted'
    return result

if __name__ == '__main__':
    stopwords = set((ROOT/'stopwords.txt').read_text(encoding='utf-8').split())
    files = sorted((ROOT/'data').glob('*.txt'))
    assert len(files) >= 10, 'At least ten documents required'
    expected, raw, filtered = reference(files,stopwords)
    actual = parse((ROOT/'results'/'inverted-index.txt').read_text(encoding='utf-8'))
    assert actual == expected, 'Posting lists differ from independent oracle'
    report = dict(status='PASS',documents=len(files),stopwords=len(stopwords),raw_tokens=raw,
                  removed_stopwords=filtered,indexed_tokens=raw-filtered,distinct_terms=len(actual),
                  postings=sum(len(v) for v in actual.values()),all_postings_match=True,
                  corpus_total=sum(sum(v.values()) for v in actual.values()))
    assert report['corpus_total'] == report['indexed_tokens']
    (ROOT/'results'/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
