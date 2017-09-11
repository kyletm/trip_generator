import os
import subprocess

def sort_by_input_column(input_path, input_file, sort_column, output_path, output_file):
   """Sort a file by a specified column.

   Inputs:
       input_path (str): Path to input file.
       input_file (str): Input file name.
       sort_column (str): Numeric column to sort.
       output_path (str): Path to output file.
       output_file: Output file name.
   """
   base_module_path = os.path.dirname(os.path.realpath(__file__))
   script_path = base_module_path + '/' + 'sort_by_input_column.r'
   subprocess.call(["C:/R/R-3.3.1/bin/Rscript.exe", script_path,
                     input_path, input_file, sort_column,
                     output_path, output_file])
                     
def cdf(weights):
    """Create CDF of weighted list.
    
    Inputs:
        weights (list): A list of numeric weights. For example, one weight
            is the number of employees in a county's industry for a given
            gender divided by the sum of the squared difference of a worker's
            income from the median income for all industries in a county for
            that worker's gender.
     
    Returns:
        cdf (list): A CDF of this weighted list.
    """
    total = sum(weights)
    cdf = []
    cumsum = 0
    for w in weights:
        cumsum += w
        cdf.append(cumsum/total)
    return cdf