# 实验二 文档倒排索引算法实现

使用 Java 和 Hadoop MapReduce，将 12 篇公开英文技术文档转换为倒排索引。
每个词对应按文件名排序的文档词频列表，以及整个语料中的总次数。

## 最终报告与实测结果

- [实验报告 PDF（7 页）](report/202400390037-张瑞泽-实验二.pdf)
- [可编辑 Word 报告](report/202400390037-张瑞泽-实验二.docx)
- [完整倒排索引](results/inverted-index.txt)
- [独立全量校验](results/validation.json)
- [实际 Hadoop 边界测试](results/edge-tests.txt)

本次在 Ubuntu 22.04.5、OpenJDK 11.0.32、Hadoop 3.4.3 上重新编译并执行，
完整语料作业 `application_1793189289440_0001` 的最终状态为 `FINISHED / SUCCEEDED`，耗时 4 分 14 秒。
12 篇文档共 45,956 个原始词次，过滤 14,142 个停词词次后保留 31,814 个词次，
生成 3,438 个不同词项、8,097 个词项与文档关联。所有倒排项与独立 Python 参考结果一致。
另一实际 Hadoop 作业覆盖大小写、标点、数字、重复词、空文件和仅含停词的文件，结果与人工预期一致。

PDF 逐页渲染检查通过，微软雅黑常规和粗体均已嵌入，仓库链接可点击。

## 目录

| 路径 | 内容 |
|---|---|
| `src/main/java/edu/lab/InvertedIndex.java` | Mapper、Reducer 和作业入口 |
| `data/` | 12 篇英文文本及来源清单 |
| `stopwords.txt` | 完整停词表，共 46 个词 |
| `scripts/build.sh` | 使用 Hadoop 自带依赖编译 Java 11 JAR |
| `scripts/run.sh` | 上传 HDFS、提交 YARN 作业、导出及验证结果 |
| `scripts/validate.py` | 独立 Python 参考统计与全量比对 |
| `scripts/test_edges.sh` | 实际 Hadoop 边界用例 |
| `results/` | 实测输出、运行日志和验证证据 |
| `report/` | 最终 PDF 报告及可编辑 Word 版本 |

## 运行环境

Linux、OpenJDK 11、Hadoop 3.4.3、Python 3（只用标准库）。
需要先配置并启动 HDFS 和 YARN；输入文本使用 UTF-8。

```bash
export HADOOP_HOME="$HOME/hadoop"
export PATH="$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"
# JAVA_HOME 按实际安装位置设置，例如 Ubuntu 的 OpenJDK 11：
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

bash scripts/build.sh
bash scripts/run.sh
bash scripts/test_edges.sh
```

`run.sh` 自动生成新的 HDFS 运行目录，也可传入只包含英文字母、数字、下划线、短横线的运行标识。
若该 HDFS 目录已存在，脚本会退出，不删除此前实验。
再次执行会覆盖本地 `results/` 下对应结果，保留重要结果前请先另存一份。

## 算法和输出

1. Mapper 从 `FileSplit` 获取文件名，用 `[A-Za-z]+` 提取连续英文字母，统一为小写，过滤停词。
2. Mapper 对保留词输出 `(word, filename)`。
3. Hadoop Shuffle 将同一单词分组。
4. Reducer 用 `TreeMap<String, Long>` 统计每篇文档次数、排序并累加总次数。

采用一个 Reducer，输出文件中的词项按字典序排列，适合本次小规模实验。
没有将最终格式化的 Reducer 用作 Combiner；两者输入输出语义不同。
这里记录的是文档内词频，不记录字符位置或词语偏移。

示例格式（仅用于解释格式，具体实测值见 `results/inverted-index.txt`）：

```text
data    <document01.txt,6>;<document02.txt,3>;<total,9>.
```

单词与列表之间为制表符；列表末尾为句点。数字、标点和连字符作为分隔符。
不做词干提取，`file` 与 `files` 是两个词项。

## 结果校验

```bash
python3 scripts/validate.py
```

校验器独立扫描保存的原始文本，使用 Python `Counter` 计算参考词频，
逐项比较全部词、文档和次数，同时检查排序、重复项、输出格式以及总次数。
`results/validation.json` 中保存最终结果。

边界测试实际提交第二个 Hadoop 作业，包含大小写、重复词、标点、数字、
空文件及仅含停词的文件，并与人工可计算的预期输出比较。

## 数据来源与许可

数据来源为 Apache Hadoop 3.4.3 官方文档，包括 HDFS、YARN、MapReduce 等主题。
完整来源网址、获取时间和 SHA-256 见 [`data/sources.json`](data/sources.json)。
正文抽取方式与分词规则见 [`data/README.md`](data/README.md)。
数据采用 Apache License 2.0；保留 [`LICENSE`](LICENSE) 与 [`NOTICE`](NOTICE)。

报告正文按作者要求采用微软雅黑、小四、1.25 倍行距，最终 PDF 不超过 8 页。
