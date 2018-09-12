final_pageranks     =   LOAD '$PAGERANKS_INPUT_PATH' USING PigStorage() AS (node: chararray, pagerank: double);
non_null            =   FILTER final_pageranks BY (pagerank is not null);
out                 =   ORDER non_null BY pagerank DESC;

rmf $OUTPUT_PATH;
STORE out INTO '/home/cloudera/Desktop/PR/project/out_node' USING PigStorage();
