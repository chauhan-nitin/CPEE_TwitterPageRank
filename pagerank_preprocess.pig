edges               =   LOAD '/home/cloudera/Desktop/PR/project/edges.csv' USING PigStorage('\t')
                        AS (from: chararray, to: chararray, weight: double);
nodes               =   GROUP edges BY from;
num_nodes           =   FOREACH (GROUP nodes ALL) GENERATE COUNT($1) AS N;


num_nodes_copy      =   FOREACH num_nodes GENERATE *;
initial_pageranks   =   FOREACH nodes GENERATE 
                            group AS node: chararray, 
                            1.0 / num_nodes_copy.N AS pagerank: double, 
                            edges.(to, weight) AS edges: {t: (to: chararray, weight: double)}, 
                            SUM(edges.weight) AS sum_of_edge_weights: double;

rmf $NUM_NODES_OUTPUT_PATH;
rmf $PAGERANKS_OUTPUT_PATH;
STORE num_nodes INTO '/home/cloudera/Desktop/PR/out_preprocessing' USING PigStorage();
STORE initial_pageranks INTO '/home/cloudera/Desktop/PR/PAGERANKS_OUTPUT_PATH' USING PigStorage();
