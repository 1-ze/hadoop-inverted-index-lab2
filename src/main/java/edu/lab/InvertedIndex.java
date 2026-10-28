package edu.lab;

import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.regex.*;
import org.apache.hadoop.conf.Configured;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.FileSplit;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.Tool;
import org.apache.hadoop.util.ToolRunner;

/** Word -> sorted document frequencies and corpus frequency. */
public class InvertedIndex extends Configured implements Tool {
    public enum Stats { TOKENS, STOPWORDS, INDEXED_TOKENS }
    public static class IndexMapper extends Mapper<Object, Text, Text, Text> {
        private static final Pattern WORD = Pattern.compile("[A-Za-z]+");
        private final Set<String> stopwords = new HashSet<>();
        private final Text term = new Text();
        private final Text document = new Text();
        @Override protected void setup(Context context) throws IOException {
            // Job.addCacheFile localizes this file for every mapper.
            for (String line : Files.readAllLines(Paths.get("stopwords.txt"), StandardCharsets.UTF_8)) {
                String word = line.trim().toLowerCase(Locale.ROOT);
                if (!word.isEmpty()) stopwords.add(word);
            }
            document.set(((FileSplit) context.getInputSplit()).getPath().getName());
        }
        @Override protected void map(Object key, Text line, Context context)
                throws IOException, InterruptedException {
            Matcher matcher = WORD.matcher(line.toString());
            while (matcher.find()) {
                context.getCounter(Stats.TOKENS).increment(1);
                String word = matcher.group().toLowerCase(Locale.ROOT);
                if (stopwords.contains(word)) {
                    context.getCounter(Stats.STOPWORDS).increment(1);
                } else {
                    term.set(word);
                    context.write(term, document);
                    context.getCounter(Stats.INDEXED_TOKENS).increment(1);
                }
            }
        }
    }
    public static class IndexReducer extends Reducer<Text, Text, Text, Text> {
        @Override protected void reduce(Text term, Iterable<Text> docs, Context context)
                throws IOException, InterruptedException {
            SortedMap<String, Long> counts = new TreeMap<>();
            long total = 0;
            for (Text doc : docs) {
                // Hadoop reuses Text instances; copy the string before retaining it.
                counts.merge(doc.toString(), 1L, Long::sum);
                total++;
            }
            StringBuilder result = new StringBuilder();
            for (Map.Entry<String, Long> entry : counts.entrySet()) {
                result.append('<').append(entry.getKey()).append(',')
                      .append(entry.getValue()).append(">;");
            }
            result.append("<total,").append(total).append(">.");
            context.write(term, new Text(result.toString()));
        }
    }
    @Override public int run(String[] args) throws Exception {
        if (args.length != 3) {
            System.err.println("Usage: InvertedIndex <input-dir> <output-dir> <stopwords-uri>");
            return 2;
        }
        Job job = Job.getInstance(getConf(), "lab2-inverted-index");
        job.setJarByClass(InvertedIndex.class);
        job.addCacheFile(new URI(args[2] + "#stopwords.txt"));
        job.setMapperClass(IndexMapper.class);
        job.setReducerClass(IndexReducer.class);
        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);
        // One reducer gives globally sorted terms for this small coursework corpus.
        job.setNumReduceTasks(1);
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
        return job.waitForCompletion(true) ? 0 : 1;
    }
    public static void main(String[] args) throws Exception {
        System.exit(ToolRunner.run(new InvertedIndex(), args));
    }
}
