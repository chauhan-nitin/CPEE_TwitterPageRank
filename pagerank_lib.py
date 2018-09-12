from org.apache.pig.scripting import Pig

class Pagerank:
    def __init__(self, edges_input, \
                       damping_factor=0.85, convergence_threshold=0.0001, max_num_iterations=20, \
                       temporary_output_prefix="/home/cloudera/Desktop/PR/project/out_data", \
                       output_path=None, \
                       preprocessing_script="/home/cloudera/Desktop/PR/project/pagerank_preprocess.pig", \
                       iteration_script="/home/cloudera/Desktop/PR/project/pagerank_iterate.pig", \
                       postprocessing_script="/home/cloudera/Desktop/PR/project/pagerank_postprocess.pig"):

        self.edges_input = edges_input
        self.damping_factor = damping_factor
        self.convergence_threshold = convergence_threshold
        self.max_num_iterations = max_num_iterations
        
        self.temporary_output_prefix = temporary_output_prefix
        self.output_path = output_path
        
        self.preprocessing_script = preprocessing_script
        self.iteration_script = iteration_script
        self.postprocessing_script = postprocessing_script

        self.preprocess_pageranks = temporary_output_prefix + "/preprocess/pageranks"
        self.preprocess_num_nodes = temporary_output_prefix + "/preprocess/num_nodes"
        self.iteration_pageranks_prefix = temporary_output_prefix + "/iteration/pageranks_"
        self.iteration_rank_changes_prefix = temporary_output_prefix + "/iteration/aggregate_rank_change_"

    def run_pagerank(self):
        """
        Calculates pageranks for directed graph of nodes and edges.

        Three main steps:
            1. Preprocessing: Process input data to:
                 a) Count the total number of nodes.
                 b) Prepare initial pagerank values for all nodes.
            2. Iteration: Calculate new pageranks for each node based on the previous pageranks of the
                          nodes with edges going into the given node.
            3. Postprocessing: Find the top pagerank nodes and join to a separate dataset to find their names.
        """
        # Preprocessing step:
        print "Starting preprocessing step."
        preprocess = Pig.compileFromFile(self.preprocessing_script)
        preprocess_params = {
            "INPUT_PATH": self.edges_input,
            "PAGERANKS_OUTPUT_PATH": self.preprocess_pageranks,
            "NUM_NODES_OUTPUT_PATH": self.preprocess_num_nodes
        }
        preprocess_bound = preprocess.bind(preprocess_params)
        preprocess_stats = preprocess_bound.runSingle()

        # Update convergence threshold based on the size of the graph (number of nodes)
        num_nodes = long(str(preprocess_stats.result("num_nodes").iterator().next().get(0)))
        convergence_threshold = long(self.convergence_threshold * num_nodes * num_nodes)
        print "Calculated convergence threshold for %d nodes: %d" % (num_nodes, convergence_threshold) 

        # Iteration step:
        iteration = Pig.compileFromFile(self.iteration_script)
        for i in range(self.max_num_iterations):
            print "Starting iteration step: %s" % str(i + 1)

            # Append the iteration number to the input/output stems
            iteration_input = self.preprocess_pageranks if i == 0 else (self.iteration_pageranks_prefix + str(i-1))
            iteration_pageranks_output = self.iteration_pageranks_prefix + str(i)
            iteration_rank_changes_output = self.iteration_rank_changes_prefix + str(i)

            iteration_bound = iteration.bind({
                "INPUT_PATH": iteration_input,
                "DAMPING_FACTOR": self.damping_factor,
                "NUM_NODES": num_nodes,
                "PAGERANKS_OUTPUT_PATH": iteration_pageranks_output,
                "AGG_RANK_CHANGE_OUTPUT_PATH": iteration_rank_changes_output
            })
            iteration_stats = iteration_bound.runSingle()

            # If we're below the convergence threshold break out of the loop.
            aggregate_rank_change = long(str(iteration_stats.result("aggregate_rank_change").iterator().next().get(0)))
            if aggregate_rank_change < convergence_threshold:
                print "Sum of ordering-rank changes %d under convergence threshold %d. Stopping." \
                       % (aggregate_rank_change, convergence_threshold)
                break
            elif i == self.max_num_iterations-1:
                print ("Sum of ordering-rank changes %d " % aggregate_rank_change) + \
                      ("above convergence threshold %d but hit max number of iterations. " % convergence_threshold) + \
                       "Stopping."
            else:
                print "Sum of ordering-rank changes %d above convergence threshold %d. Continuing." \
                       % (aggregate_rank_change, convergence_threshold)

        iteration_pagerank_result = self.iteration_pageranks_prefix + str(i)

        # Postprocesing step:
        print "Starting postprocessing step."
        postprocess = Pig.compileFromFile(self.postprocessing_script)
        postprocess_params = { "PAGERANKS_INPUT_PATH": iteration_pagerank_result }
        if self.output_path is not None: # otherwise, the script outputs to the default location,
                                         # which is a special directory in s3://mortar-example-output-data
                                         # permissioned for your Mortar account.
            postprocess_params["OUTPUT_PATH"] = self.output_path
        postprocess_bound = postprocess.bind(postprocess_params)
        postprocess_stats = postprocess_bound.runSingle()
