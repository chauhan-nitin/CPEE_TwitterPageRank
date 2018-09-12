from pagerank_lib import Pagerank

# A directed graph with the schema "from, to, weight" and a tab delimiter.
EDGES_INPUT = "/home/cloudera/Desktop/PR/project/out_node"

# Iteration Parameters -- see README.md for more information
DAMPING_FACTOR        = 0.85
CONVERGENCE_THRESHOLD = 0.0015 # we set the convergence parameter higher than usual, for sake of speeding up the example
MAX_NUM_ITERATIONS    = 20

# Temporary data is stored in HDFS for better performance
TEMPORARY_OUTPUT_PREFIX = "/home/cloudera/Desktop/PR/temp"

# By default, final output is sent to the S3 bucket mortar-example-output-data,
# in a special directory permissioned for your account.
# See my-pagerank.py for an example of outputting to your own S3 bucket.

if __name__ == "__main__":
    pagerank = Pagerank(EDGES_INPUT,
                        damping_factor=DAMPING_FACTOR,
                        convergence_threshold=CONVERGENCE_THRESHOLD,
                        max_num_iterations=MAX_NUM_ITERATIONS,
                        temporary_output_prefix=TEMPORARY_OUTPUT_PREFIX)
    pagerank.run_pagerank()
