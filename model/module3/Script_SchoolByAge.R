library(data.table)
data = fread("CaliforniaModule3NN_AssignedSchoolCounty.csv")
Ages = 5:24
results = matrix(data = NA, nrow = 21, ncol = 10)
colnames(results) = c("publicCount", "privateCount", "total_LowerSchool", "fourYearCount", "twoYearCount", "nonDegCount", "totalPostSecondary", "totalStudents", "totalNonStudents", "totalPeople_OfThisAge")
rownames(results) = c(5:24, "total")
normalizeAge = 4
for(age in Ages)
{
	rowIndex = age - normalizeAge
	print(paste("working on the age: ", str(age), sep = ""))
	ageSubset = subset(data, data$Age == eval(age))
	nonStudent = subset(ageSubset, ageSubset$Type1 == "non student")
	student = subset(ageSubset, ageSubset$Type1 != "non student")
	results[rowIndex, 1] = nrow(subset(student, student$Type2 == "public"))
	results[rowIndex, 2] = nrow(subset(student, student$Type2 == "private"))
	results[rowIndex, 3] = results[rowIndex, 1] + results[rowIndex, 2]
	results[rowIndex, 4] = nrow(subset(student, student$Type2 == "four year"))
	results[rowIndex, 5] = nrow(subset(student, student$Type2 == "two year"))
	results[rowIndex, 6] = nrow(subset(student, student$Type2 == "non deg"))
	results[rowIndex, 7] = results[rowIndex, 4] + results[rowIndex, 5] + results[rowIndex, 6]
	results[rowIndex, 8] = results[rowIndex, 7] + results[rowIndex, 3]
	results[rowIndex, 9] = nrow(nonStudent)
	results[rowIndex, 10] = results[rowIndex, 9] + results[rowIndex, 8]
}

lastRow = nrow(results)
for(colIndex in 1:10)
{
	results[lastRow, colIndex] = sum(results[1:(lastRow-1),colIndex])
}

write.csv(results,  file = "/Users/matthewgarvey/Desktop/Module3/StudentsByAge.csv",  row.names = TRUE)