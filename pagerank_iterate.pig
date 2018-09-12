DEFINE Enumerate datafu.pig.bags.Enumerate('1');
INPUT_PATH="/home/cloudera/Desktop/PR/out_preprocessing"
previous_pageranks      =   LOAD '$INPUT_PATH' USING PigStorage('\t')
                            AS (node: chararray, 
                                pagerank: double, 
                                edges: {t: (to: chararray, weight: double)},
                                sum_of_edge_weights: double);

outbound_pageranks_temp =   FOREACH previous_pageranks GENERATE
                                FLATTEN(edges) AS (to: chararray, weight: double),
                                sum_of_edge_weights,
                                pagerank AS source_pagerank;

outbound_pageranks      =   FOREACH outbound_pageranks_temp GENERATE
                                to, (weight / sum_of_edge_weights) * source_pagerank AS pagerank;

cogrouped               =   COGROUP previous_pageranks BY node, outbound_pageranks BY to;
new_pageranks           =   FOREACH cogrouped GENERATE
                                group AS node,
                                ((1.0 - $DAMPING_FACTOR) / $NUM_NODES)
                                    + $DAMPING_FACTOR * SUM(outbound_pageranks.pagerank) AS pagerank,
                                FLATTEN(previous_pageranks.edges) AS edges,
                                FLATTEN(previous_pageranks.sum_of_edge_weights) AS sum_of_edge_weights;

previous_projected      =   FOREACH previous_pageranks GENERATE node, pagerank;
previous_ordered        =   ORDER previous_projected BY pagerank DESC;
previous_enumerated     =   FOREACH (GROUP previous_ordered ALL)
                            GENERATE FLATTEN(Enumerate($1)) AS (node, pagerank, rank);

new_projected           =   FOREACH new_pageranks GENERATE node, pagerank;
new_ordered             =   ORDER new_projected BY pagerank DESC;
new_enumerated          =   FOREACH (GROUP new_ordered ALL)
                            GENERATE FLATTEN(Enumerate($1)) AS (node, pagerank, rank);

old_vs_new_ranks        =   JOIN previous_enumerated BY node, new_enumerated BY node;
rank_changes            =   FOREACH old_vs_new_ranks
                            GENERATE ABS(new_enumerated::rank - previous_enumerated::rank);
aggregate_rank_change   =   FOREACH (GROUP rank_changes ALL) GENERATE SUM($1);

rmf $PAGERANKS_OUTPUT_PATH;
rmf $AGG_RANK_CHANGE_OUTPUT_PATH;
STORE new_pageranks INTO '/home/cloudera/Desktop/PR/PAGERANKS_ITERATE_PATH' USING PigStorage();
STORE aggregate_rank_change INTO '$AGG_RANK_CHANGE_OUTPUT_PATH' USING PigStorage();
