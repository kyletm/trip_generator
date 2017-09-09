# script to sort the workers that work in the state that is passed by argument by working county
args = commandArgs(trailingOnly = TRUE)
inputPath = args[1]
inputFile = args[2]
columnSort = as.numeric(args[3])
outputPath = args[4]
outputFile = args[5]
library("bit64")
library("data.table")
print("reading in file")
people = fread(paste(inputPath,  inputFile, sep = ""))
print("finshed reading in file")
print("ordering file by some criterion") 
people = people[order(people[[columnSort]]),]
print("finished sorting file")
print("starting to write sorted data out to a file")
write.csv(people,  file = paste(outputPath, outputFile, sep = ""),  row.names = FALSE)
print("done writing the sorted output")