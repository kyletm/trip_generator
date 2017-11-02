# script to sort files by specific columns - used for FIPS sorting to
# enhance overall runtime and reduce distribution regeneration
# see: https://stackoverflow.com/questions/13685295/
# sort-a-data-table-fast-by-ascending-descending-order
# for speed reasons as to why this is used instead of a python equivalent
print(.libPaths())
if(!require("bit64")){install.packages("bit64", repos="http://cran.us.r-project.org")}
if(!require("data.table")){install.packages("data.table", repos="http://cran.us.r-project.org")}
args = commandArgs(trailingOnly = TRUE)
input_path = args[1]
input_file = args[2]
column_sort = as.numeric(args[3])
output_path = args[4]
output_file = args[5]
library("bit64")
library("data.table")
print("reading in file")
file = fread(paste(input_path, input_file, sep = ""))
print("finshed reading in file")
print("ordering file by some criterion") 
file = file[order(file[[column_sort]]),]
print("finished sorting file")
print("starting to write sorted data out to a file")
write.csv(file,  file = paste(output_path, output_file, sep = ""),  row.names = FALSE)
print("done writing the sorted output")
