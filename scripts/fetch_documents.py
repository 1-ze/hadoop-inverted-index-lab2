"""Download 12 Apache Hadoop documentation pages (Apache License 2.0).
Standard library only; remove site navigation and extract the main article.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import json
import re
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
VERSION = '3.4.3'
PAGES = [
 ('Hadoop single node setup', 'hadoop-project-dist/hadoop-common/SingleCluster.html'),
 ('Hadoop cluster setup', 'hadoop-project-dist/hadoop-common/ClusterSetup.html'),
 ('HDFS architecture', 'hadoop-project-dist/hadoop-hdfs/HdfsDesign.html'),
 ('HDFS user guide', 'hadoop-project-dist/hadoop-hdfs/HdfsUserGuide.html'),
 ('Hadoop filesystem shell', 'hadoop-project-dist/hadoop-common/FileSystemShell.html'),
 ('MapReduce tutorial', 'hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html'),
 ('YARN architecture', 'hadoop-yarn/hadoop-yarn-site/YARN.html'),
 ('Hadoop Streaming', 'hadoop-streaming/HadoopStreaming.html'),
 ('Hadoop archive guide', 'hadoop-archives/HadoopArchives.html'),
 ('DistCp guide', 'hadoop-distcp/DistCp.html'),
 ('HDFS snapshots', 'hadoop-project-dist/hadoop-hdfs/HdfsSnapshots.html'),
 ('HDFS high availability with QJM', 'hadoop-project-dist/hadoop-hdfs/HDFSHighAvailabilityWithQJM.html'),
]

class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.active = False
        self.depth = 0
        self.skip = 0
        self.text = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and attrs.get('id') == 'bodyColumn':
            self.active = True
            self.depth = 1
            return
        if self.active:
            if tag == 'div': self.depth += 1
            if tag in ('script', 'style'): self.skip += 1
            if tag in ('p','li','h1','h2','h3','h4','tr','pre','br'): self.text.append('\n')
    def handle_endtag(self, tag):
        if not self.active: return
        if tag == 'div':
            self.depth -= 1
            if self.depth == 0: self.active = False
        if tag in ('script','style'): self.skip = max(0, self.skip-1)
        if tag in ('p','li','h1','h2','h3','h4','tr','pre'): self.text.append('\n')
    def handle_data(self, data):
        if self.active and not self.skip: self.text.append(data)

def fetch(item):
    idx, (title, relative) = item
    url = f'https://hadoop.apache.org/docs/r{VERSION}/{relative}'
    with urlopen(Request(url, headers={'User-Agent':'Coursework-Index-Lab/1.0'}), timeout=60) as response:
        html = response.read().decode('utf-8')
    parser = ArticleParser()
    parser.feed(html)
    lines = [re.sub(r'\s+', ' ', line).strip() for line in ''.join(parser.text).splitlines()]
    text = '\n'.join(line for line in lines if line) + '\n'
    if len(re.findall(r'[A-Za-z]+', text)) < 100:
        raise RuntimeError(f'Missing or short article: {url}')
    filename = f'document{idx:02d}.txt'
    content = text.encode('utf-8')
    (ROOT/'data'/filename).write_bytes(content)
    return dict(filename=filename,title=title,url=url,downloaded_at=datetime.now(timezone.utc).isoformat(),
                bytes=len(content),sha256=sha256(content).hexdigest(),license='Apache-2.0',
                tokens=len(re.findall(r'[A-Za-z]+',text)))

if __name__ == '__main__':
    (ROOT/'data').mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(fetch, enumerate(PAGES,1)))
    (ROOT/'data'/'sources.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'documents':len(rows),'tokens':sum(r['tokens'] for r in rows)},indent=2))
