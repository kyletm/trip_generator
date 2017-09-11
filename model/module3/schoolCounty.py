'''
schoolCounty.py

Project: United States Trip File Generation - Module 3
Author: Wyrough
version date: 9/17/2016
Python 3.5

Purpose: This is the helper module for module3, which assigns each student a proper place of school. This module creates and designs a school County
object that houses all the enrollment data for a particular county and its geographical neighbors. It provides methods to select a county of schooling,
and then a particular school given that county and type of school.

Notes: 
'''
import countyAdjacencyReader
import csv
import cdf
import math
import random
import bisect

'------------------------GLOBAL DATA------------------------'
'File Location of School Data'
schoolDataBase = 'D:/Data/Schools/School Database'
'-----------------------------------------------------------'


'SchoolCounty Object: An object for housing the entire school data for a particular county, and points to its neighbors. '
class schoolCountyAssigner:
	def __init__(self, fips, bachormore, assoc, non):
		'Initialize County Geography'
		self.fips = fips
		self.county = countyAdjacencyReader.read_data(fips)
		self.county.set_lat_lon()
		'Read Post-Secondary Schools'
		self.twoyear, self.fouryear, self.nondeg = self.read_post_sec_schools_for_county(fips)
		'Read All Public Schools'
		self.elempublic, self.midpublic, self.highpublic = self.read_public_schools(fips)
		'Read All Private Schools'
		self.elemprivate, self.midprivate, self.highprivate = self.read_private_schools(fips)
		'Get seats for public schools by age demographic and for all private schools in our county'
		self.publicElemSeats, self.publicMiddleSeats, self.publicHighSeats, self.privateElemSeats, self.privateMiddleSeats, self.privateHighSeats = self.get_total_seats()
		'Create Distributions for:'
		'1.) public schools (nothing right now ... just choosing the closest public school without doing any pre-processing ahead of time)'
		'...'
		'2.) private school disitrbutions by age demographic within aa partic '
		self.schoolCountyList = [];
		self.privateElemCounties = [];
		self.privateMiddleCounties = [];
		self.privateHighCounties = [];
		self.distPrivElem, self.distPrivMiddle, self.distPrivHigh = assemble_privateCounty_dist()
		'3.) post-secondary edcuation by demographic within a county'
		self.fouryearDist, self.twoyearDist, self.nonDegreeDist = assemble_postsec_dist(bachormore, assoc, non)
		

	def assemble_privateCounty_dist(self):
		distPrivElem = [];
		distPrivMiddle = [];
		distPrivHigh = [];
		[distPrivElem.append(int(school[7]) / self.privateElemSeats) for school in self.elemprivate]
		[distPrivMiddle.append(int(school[7]) / self.privateMiddleSeats) for school in self.midprivate]
		[distPrivHigh.append(int(school[7]) / self.privateHighSeats) for school in self.highprivate]
		distPrivElem = cdf(distPrivElem)
		distPrivMiddle = cdf(distPrivMiddle)
		distPrivHigh = cdf(distPrivHigh)
		return distPrivElem, distPrivMiddle, distPrivHigh


	'Find and Put the Neighbors of Home County and the Home County into distributions'
	def assemble_neighborly_dist(self):
		privateSchoolCounties = []
		for j in self.county.neighbors:
			privateSchoolCounties.append(schoolCounty(j))
		privateSchoolCounties.append(self)
		self.schoolCountyList = privateSchoolCounties
		'Create the distributions from the neighbors for the different age demographics.'
		privateElemCounties = []; 
		privateMiddleCounties = [];
		privateHighCounties = [];
		homelat, homelon = (self.county).get_lat_lon
		minDistance = sys.maxint
		for schoolcounty in privateSchoolCounties:
			if schoolcounty is self:
				continue
			distanceCounty = distance_between_points(homelat, homelon, (schoolcounty.county).lat, (schoolcounty.county).lon)
			privateElemCounties.append(schoolcounty.privateElemSeats / distanceCounty**2)
			privateMiddleCounties.append(schoolcounty.privateMiddleSeats / distanceCounty**2)
			privateHighCounties.append(schoolcounty.privateHighSeats / distanceCounty**2)
			if distanceCounty < minDistance:
				minDistance = distanceCounty
		privateElemCounties.append(self.privateElemSeats / (minDistance * 0.75)**2)
		privateMiddleCounties.append(self.privateMiddleSeats / (minDistance * 0.75)**2)
		privateHighCounties.append(self.privateHighSeats / (minDistance * 0.75)**2)
		self.privateElemCounties = cdf(privateElemCounties)
		self.privateMiddleCounties = cdf(privateMiddleCounties)
		self.privateHighCounties = cdf(privateHighCounties)


	def assemble_postsec_dist(self, bachormore, assoc, non):
		fouryearDist = [];
		twoyearDist = [];
		nonDegreeDist = [];
		fouryearEnrollment, twoyearEnrollment, nonEnrollment = self.scale_school_employment_to_students(bachormore, assoc, non)
		fouryearDist = cdf(fourYearEnrollment)
		twoyearDist = cdf(twoYearEnrollment)
		nonDegreeDist = cdf(nonEnrollment)
		self.fouryearDist = fouryearDist
		self.twoyearDist = twoyearDist
		self.nonDegreeDist = nonDegreeDist


	'Calculate the Total Enrollment of a County'
	def get_total_seats(self):
		publicElem = 0
		publicMiddle = 0
		publicHigh = 0
		privateElem = 0
		privateMiddle = 0
		privateHigh = 0
		for k in self.elempublic:
			publicElem += int(k[5])
		for k in self.midpublic:
			publicMiddle += int(k[5])
		for k in self.highpublic:
			publicHigh += int(k[5])
		for k in self.elemprivate:
			privateElem += int(k[7])
		for k in self.midprivate:
			privateMiddle += int(k[7])
		for k in self.highprivate:
			privateHigh += int(k[7])
		return publicElem, publicMiddle, publicHigh, privateElem, privateMiddle, privateHigh
		
	'Create a Distribution of All Counties relative to Home County'
	def school_county_dist(self):
		options = []
		idx = 0
		seats = 0
		for j in self.neighborlyschools:
			for k in j.elempublic:
				seats += int(k[5])
			for k in j.midpublic:
				seats += int(k[5])
			for k in j.highpublic:
				seats+= int(k[5])
			for k in j.elemprivate:
				seats += int(k[7])
			for k in j.midprivate:
				seats += int(k[7])
			for k in j.highprivate:
				seats +=int(k[7])
			options.append([idx, j.fips, seats, distance_between_counties(self.county.lat, self.county.lon, j.county.lat, j.county.lon)])
			seats = 0
			idx+=1
		self.options = options

	'If the county chosen is a neighboring County to the student\'s home county, then returns returns a reference to an instance of the class schoolCounty for that neighboring County.'
	'Else if the county chosen is the home county, this instance method returns the String \'home county\' ' 
	def select_school_county(self, type1, type2):  
		if len(self.county.neighbors) == 0:
			return 'home county'
		elif type2 == 'public':
			return 'home county'
		else:
			newOptions = []
			idx = 0
			seats = 0
			for j in self.neighborlyschools:
				if type2 == 'private':
					if type1 == 'elem':
						if len(j.elemprivate) == 0: newOptions.append([idx, j.fips, 0, 1000])
						else: newOptions.append(self.options[idx])
					elif type1 == 'mid':
						if len(j.midprivate) == 0: newOptions.append([idx, j.fips, 0, 1000])
						else: newOptions.append(self.options[idx])
					elif type1 == 'high':
						if len(j.highprivate) == 0: newOptions.append([idx, j.fips, 0, 1000])
						else: newOptions.append(self.options[idx])
				else:
					newOptions.append(self.options[idx])
				idx += 1
			seatsAttractiveness = [float(j[2]) for j in newOptions]
			if type2 == 'private':
				if type1 == 'elem': 
					if len(self.elemprivate) != 0:
						dists.append(float(self.totalseats) / (min(allDistances) * 0.750)**2)
				elif type1 == 'mid':
					if len(self.midprivate) != 0:
						dists.append(float(self.totalseats) / (min(allDistances) * 0.750)**2)
				elif type1 == 'high':
					if len(self.highprivate) != 0:
						dists.append(float(self.totalseats) / (min(allDistances) * 0.750)**2)
			if type2 == 'public':
				if type1 == 'elem': 
					if len(self.elempublic) != 0:
						dists.append(float(self.totalseats) / (min(allDistances) * 0.750)**2)
				elif type1 == 'mid':
					if len(self.midpublic) != 0:
						dists.append(float(self.totalseats) / (min(allDistances) * 0.750)**2)
				elif type1 == 'high':
					if len(self.highpublic) != 0:
						dists.append(float(self.totalseats) / (min(allDistances) * 0.750)**2)
			if sum(dists) == 0:
				return 'change'
			if sum(dists) != 0:
				dists = [j / sum(dists) for j in dists]
			weights = cdf(dists)
			split = random.random()
			idx=bisect.bisect(weights,split)
			if idx == len(self.options):
				return ('home county')
			else:
				return (self.neighborlyschools[idx])

	'For Each Post-Secondary School List, Scale The Employee Numbers to Student Enrollment'
	'Gives for us the number of students in each type of program from each school'
	def scale_school_employment_to_students(self, statefouryear, statetwoyear, statenodeg):
		countyfouryear, countytwoyear, countynodeg = get_scale_factor(self.fips, self.county.statecode, statefouryear, statetwoyear, statenodeg)
		totalEmployment = []
		[totalEmployment.append(int(j[len(j) - 4])) for j in self.fouryear]
		totalFourEmployment = sum(totalEmployment)
		totalEmployment = []        
		[totalEmployment.append(int(j[len(j) - 4])) for j in self.twoyear]
		totalTwoEmployment = sum(totalEmployment)
		totalEmployment = []
		[totalEmployment.append(int(j[len(j) - 4])) for j in self.nondeg]
		totalNonEmployment = sum(totalEmployment)
		count = 0
		fouryearEnrollment = []; twoyearEnrollment = []; nonEnrollment = []
		for j in self.fouryear:
			j[len(j) - 4] = int((float(j[len(j) - 4]) / totalFourEmployment) * countyfouryear)
			fouryearEnrollment.append([count, j[len(j) - 4]])
			count+=1
		count = 0
		for j in self.twoyear:
			j[len(j) - 4] = int((float(j[len(j) - 4]) / totalTwoEmployment) * countytwoyear)
			twoyearEnrollment.append([count, j[len(j) - 4]])
			count+=1
		count = 0
		for j in self.nondeg:
			j[len(j) - 4] = int((float(j[len(j) - 4]) / totalNonEmployment) * countynodeg)
			nonEnrollment.append([count, j[len(j) - 4]])
			count+=1
		return fouryearEnrollment, twoyearEnrollment, nonEnrollment
	   

	'Select an Individual School For a Student' 
	def get_school_by_type(self, type1, type2, homelat, homelon):
		if type1 == 'elem' or type1 == 'mid' or type1 == 'high':
			county = self.select_school_county(type1, type2)
			if county == 'change':
				type2 = 'public'
				county = self.select_school_county(type1, type2)
			if county == 'change':
				return 0
			if type2 == 'public':
				if type1 == 'elem':
					if county == 'home county': 
						idx, school = drawSchool(self.elempublic, homelat, homelon); 
						if self.elempublic[idx][5] > 1: self.elempublic[idx][5]-=1
					else: 
						idx, school = drawSchool(county.elempublic, homelat, homelon); 
						if county.elempublic[idx][5] > 1: county.elempublic[idx][5]-=1
				elif type1 == 'mid':
					if county == 'home county': 
						idx, school = drawSchool(self.midpublic, homelat, homelon); 
						if self.midpublic[idx][5] > 1: self.midpublic[idx][5]-=1
					else: 
						idx, school = drawSchool(county.midpublic, homelat, homelon); 
						if county.midpublic[idx][5] > 1: county.midpublic[idx][5]-=1
				elif type1 == 'high':
					if county == 'home county': 
						idx, school = drawSchool(self.highpublic, homelat, homelon); 
						if self.highpublic[idx][5] > 1: self.highpublic[idx][5]-=1
					else: 
						idx, school = drawSchool(county.highpublic, homelat, homelon); 
						if county.highpublic[idx][5] > 1: county.highpublic[idx][5]-=1
			elif type2 == 'private':  
				if type1 == 'elem':
					if county == 'home county': 
						if len(self.elemprivate) != 0:
							idx, school = drawSchool(self.elemprivate, homelat, homelon); 
							if self.elemprivate[idx][7] > 1: self.elemprivate[idx][7]-=1
						elif len(self.elemprivate) == 0:
							idx, school = drawSchool(self.elempublic, homelat, homelon);
						else:
							if len(county.elemprivate) == 0:
								idx, school = drawSchool(county.elempublic, homelat, homelon)
							else: 
								idx, school = drawSchool(county.elemprivate, homelat, homelon); 
								if county.elemprivate[idx][7] > 1: county.elemprivate[idx][7]-=1
				elif type1 == 'mid':
					if county == 'home county': 
						if len(self.midprivate) != 0:
							idx, school = drawSchool(self.midprivate, homelat, homelon); 
							if (self.midprivate[idx][7] > 1): self.midprivate[idx][7]-=1
						elif len(self.midprivate) == 0:
							idx, school = drawSchool(self.midpublic, homelat, homelon)
						else:
							if len(county.midprivate) == 0:
								idx, school = drawSchool(county.midpublic, homelat, homelon)
							else: 
								idx, school = drawSchool(county.midprivate, homelat, homelon); 
								if (county.midprivate[idx][7] > 1): county.midprivate[idx][7]-=1
				elif type1 == 'high':
					if county == 'home county':
						if len(self.highprivate) != 0: 
							idx, school = drawSchool(self.highprivate, homelat, homelon); 
							if (self.highprivate[idx][7] > 1): self.highprivate[idx][7]-=1
						elif len(self.highprivate) == 0:
							idx, school = drawSchool(self.highpublic, homelat, homelon)
						else: 
							if county.highprivate == 0:
								idx, school = drawSchool(county.highpublic, homelat, homelon)
							else:
								idx, school = drawSchool(county.highprivate, homelat, homelon)
							if (county.highprivate[idx][7] > 1): county.highprivate[idx][7]-=1
		elif type1 == 'college' or type1 == 'on campus college':
			if type2 == 'four year':
				try:
					school = self.drawCollege(self.fouryeardist, self.fouryear, homelat, homelon)
				except (ZeroDivisionError, IndexError): 
					for j in self.neighborlyschools:
						try:
							school = j.drawCollege(j.fouryeardist, j.fouryear, homelat, homelon)
							break
						except (ZeroDivisionError, IndexError):
							test = True
			elif type2 == 'two year':
				try:
					school = self.drawCollege(self.twoyeardist, self.twoyear, homelat, homelon)
				except (ZeroDivisionError, IndexError):
					for j in self.neighborlyschools:
						try:
							school = j.drawCollege(j.fouryeardist, j.fouryear, homelat, homelon)
							break
						except (ZeroDivisionError, IndexError):
							test = True
			elif type2 == 'non deg':
				try:
					school = self.drawCollege(self.nondist, self.nondeg, homelat, homelon)
				except(ZeroDivisionError, IndexError):
					for j in self.neighborlyschools:
						try:
							school = j.drawCollege(j.nondist, j.nondeg, homelat, homelon)
							break
						except (ZeroDivisionError, IndexError):
							test = True
		elif type1 == 'non student':
			return 1
		else:
			return 0
		try:
			return school
		except UnboundLocalError:
			return 0
	
	'Draw College Institution From List'
	def drawCollege(self, schoolList, schools, homelat, homelon):
		weights= []
		[weights.append(float(j[1]) / (distance_between_counties(float(j[len(j)-2]), float(j[len(j)-1]), homelat, homelon)**2)) for j in schoolList]
		cdf2 = cdf(weights)
		split = random.random()
		idx = bisect.bisect(cdf2, split)
		return schools[idx]
	
	'Initialize Public Schools For County'
	def read_public_schools(self, fips):
		fileLocationElem = schoolDataBase + 'CountyPublicSchools/' +  'Elem/'
		fileLocationMid = schoolDataBase + 'CountyPublicSchools/' +  'Mid/'
		fileLocationHigh = schoolDataBase + 'CountyPublicSchools/' +  'High/'
		try:
			elem = open(fileLocationElem + fips + 'Elem.csv', 'r')
			elempublicschools = csv.reader(elem, delimiter = ',')
		except IOError:
			elem = None
		try:
			mid = open(fileLocationMid + fips + 'Mid.csv', 'r')
			midpublicschools = csv.reader(mid, delimiter = ',')
		except IOError:
			mid = None
		try:
			high = open(fileLocationHigh + fips + 'High.csv', 'r')
			highpublicschools = csv.reader(high, delimiter = ',')
		except IOError:
			high = None
		elempublic = []; midpublic = []; highpublic = []
		if elem != None:
			[elempublic.append(row) for row in elempublicschools]
			for j in elempublic: j[5] = int(j[5])
		if mid != None:
			[midpublic.append(row) for row in midpublicschools]
			for j in midpublic: j[5] = int(j[5])
		if high != None:
			[highpublic.append(row) for row in highpublicschools]
			for j in highpublic: j[5] = int(j[5])
		return elempublic, midpublic, highpublic

	'Initialize Private Schools For County'
	def read_private_schools(self, fips):
		fileLocation = schoolDataBase + 'CountyPrivateSchools/'
		try:
			elem = open(fileLocation + fips + 'Private.csv', 'r')
			elemprivateschools = csv.reader(elem, delimiter = ',')
		except IOError:
			elem = None
		elemprivate = []; midprivate = []; highprivate = []
		if elem != None:
			for j in elemprivateschools: j[7] = int(j[7])
			for row in elemprivateschools:
				if row[6] == '1':
					elemprivate.append(row)
				if row[6] == '2' or row[6] == '3':
					highprivate.append(row)
		midprivate = highprivate
		return elemprivate, highprivate, highprivate    
   
	'Initialize Post Secondary Schools for county'
	def read_post_sec_schools_for_county(self, fips):
		countyAbbrev = self.county.stateabbrev
		fileLocation = schoolDataBase + 'PostSecSchoolsByCounty/' + countyAbbrev + '/' + str(fips) + '_' + countyAbbrev + '_'
		try:
			twoyear = open(fileLocation + 'CommunityCollege.csv', 'r')
			twoyearschools = csv.reader(twoyear, delimiter=',')
		except IOError:
			twoyear = None
		try:
			fouryear = open(fileLocation + 'University.csv', 'r')
			fouryearschools = csv.reader(fouryear, delimiter=',')
		except IOError:
			fouryear = None
		try:
			nondeg = open(fileLocation + 'NonDegree.csv', 'r')
			nondegschools = csv.reader(nondeg, delimiter=',')
		except IOError:
			nondeg = None
		allNonDegSchools = []; allTwoYearSchools = []; allFourYearSchools = []
		if twoyear != None:
			for row in twoyearschools: allTwoYearSchools.append(row)
		if fouryear != None:
			for row in fouryearschools: allFourYearSchools.append(row)
		if nondeg != None:
			for row in nondegschools: allNonDegSchools.append(row)
		return allTwoYearSchools, allFourYearSchools, allNonDegSchools

'SELECT (NON-SECONDARY) SCHOOL FROM LIST USING ASSEMBLED DISTIRBUTION'
def drawSchool(schoolList, homelat, homelon):
	weights = []
	if len(schoolList[0]) == 11:
		[weights.append(float(j[5]) / (distance_between_counties(j[6], j[7], homelat, homelon))**2) for j in schoolList]
		alldist = []
		[alldist.append(distance_between_counties(j[6], j[7], homelat, homelon)) for j in schoolList]
		#return schoolList[alldist.index(min(alldist))]
	else:
		[weights.append(float(j[7]) / (distance_between_counties(j[4], j[5], homelat, homelon))**2) for j in schoolList]
	cdf2 = cdf(weights)
	split = random.random()
	idx = bisect.bisect(cdf2, split)
	return idx, schoolList[idx]

'RETURN MILES BETWEEN LATITUDE AND LONGITUDE POINTS '
def distance_between_points(lat1, lon1, lat2, lon2):
	degrees_to_radians = math.pi/180.0
	phi1 = (90.0 - float(lat1))*degrees_to_radians
	phi2 = (90.0 - float(lat2))*degrees_to_radians
	theta1 = float(lon1)*degrees_to_radians
	theta2 = float(lon2)*degrees_to_radians
	cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
		   math.cos(phi1)*math.cos(phi2))
	arc = math.acos(cos)
	return arc * 3963.167

'Scale State Enrollment in Types of Post-Sec Schools by County Population'
'To Obtain County Enrollment in Different Programs'
def get_scale_factor(fips, state, statefouryear, statetwoyear, statenodeg):
	statecounties = []
	C_PATH = "C:\\Users\\Hill\\Desktop\\Thesis\\Data\\WorkFlow"
	fname = C_PATH + '\\allCounties.txt'
	f = open(fname, 'r')
	totalStatePop = 0.0
	countyPop = []
	weights = []
	for line in f:
		splitter = line.split(',')
		'In State'
		if (splitter[1] == state):
			if splitter[3] not in statecounties:
				statecounties.append(splitter[3])
				totalStatePop+=float(splitter[7])
				countyPop.append([splitter[3], splitter[7]])
	for j in countyPop:
		weights.append([j[0], float(j[1])/totalStatePop])
		if j[0] == fips:
			req = (weights.pop())
	countyfouryear = req[1]*statefouryear
	countytwoyear = req[1]*statetwoyear
	countynodeg = req[1]*statenodeg
	return countyfouryear, countytwoyear, countynodeg