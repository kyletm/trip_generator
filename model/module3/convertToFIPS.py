def convertToFIPS(countyCode):
	countyCode = str(countyCode)
	if len(countyCode) == 5:
		return countyCode
	else:
		if len(countyCode) == 4:
			countyCode = '0' + countyCode
			if len(countyCode) != 5:
				print('FATAL ERROR: COUNTY CODE INCORRECTLY FORMED')
	return countyCode