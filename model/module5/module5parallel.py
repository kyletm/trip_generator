# -*- coding: utf-8 -*-
"""
Created on Tue May  9 15:37:22 2017

@author: Kyle
"""

#!/usr/bin/env python


import os, sys
import os.path
import argparse
import multiprocessing
import csv
import activityPattern
import findOtherTrips
import classDumpModule5
from datetime import datetime
import pandas as pd
import statistics

'----------PATH DEFINITIONS---------------------'
#rootDrive = 'E'
rootFilePath = 'D:/Data/Output/'
inputFileNameSuffix = 'Module4NN2ndRun.csv'
tempSuffix = 'Module5Temp.csv'
tempSuffixNoFile = 'Module5Temp'
outputFileNameSuffix = 'Module5NN1stRun.csv'

#dataDrive = 'E'
dataRoot = 'D:/Data/'
'-----------------------------------------------'

def writeHeaders2(pW):
    """ 
    Summary:
    Writes headers for split-node files.
    
    Input Arguments:    
    pW: A csv.writer object
    """
    pW.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor'] + ['Node Name']
                + ['Node County'] + ['Node Lat'] + ['Node Lon'] + ['Node Industry']
                + ['XCoord'] + ['YCoord'] + ['Segment'] + ['Row'] + ['IsComplete'])
                
def writeHeaders1(pW):
    """ 
    Summary:
    Writes headers for final Module 5 Output files.
    
    Input Arguments:    
    pW: A csv.writer object
    """
    pW.writerow(['Residence State'] + ['County Code'] + ['Tract Code'] + ['Block Code'] + ['HH ID'] 
                + ['Person ID Number'] + ['Activity Pattern']
                + ['Node 1 Type'] + ['Node 1 Predecessor'] + ['Node 1 Successor'] + ['Node 1 Name'] + ['Node 1 County'] + ['Node 1 Lat'] + ['Node 1 Lon'] + ['Node 1 Industry']
                + ['Node 2 Type'] + ['Node 2 Predecessor'] + ['Node 2 Successor'] + ['Node 2 Name'] + ['Node 2 County'] + ['Node 2 Lat'] + ['Node 2 Lon'] + ['Node 2 Industry']
                + ['Node 3 Type'] + ['Node 3 Predecessor'] + ['Node 3 Successor'] + ['Node 3 Name'] + ['Node 3 County'] + ['Node 3 Lat'] + ['Node 3 Lon'] + ['Node 3 Industry']
                + ['Node 4 Type'] + ['Node 4 Predecessor'] + ['Node 4 Successor'] + ['Node 4 Name'] + ['Node 4 County'] + ['Node 4 Lat'] + ['Node 4 Lon'] + ['Node 4 Industry']
                + ['Node 5 Type'] + ['Node 5 Predecessor'] + ['Node 5 Successor'] + ['Node 5 Name'] + ['Node 5 County'] + ['Node 5 Lat'] + ['Node 5 Lon'] + ['Node 5 Industry']
                + ['Node 6 Type'] + ['Node 6 Predecessor'] + ['Node 6 Successor'] + ['Node 6 Name'] + ['Node 6 County'] + ['Node 6 Lat'] + ['Node 6 Lon'] + ['Node 6 Industry']
                + ['Node 7 Type'] + ['Node 7 Predecessor'] + ['Node 7 Successor'] + ['Node 7 Name'] + ['Node 7 County'] + ['Node 7 Lat'] + ['Node 7 Lon'] + ['Node 7 Industry'])

def correct_FIPS(state, county):
    """ 
    Summary:
    Corrects issues with FIPS codes by left-padding
    FIPS when zeros are missing, adjusts for issues with
    2010 Census vs. Data with Hawaii FIPS 15009
    
    Input Arguments:    
    person: A row from Module4NN, detailing a person's activity
    
    Output:
    A corrected/adjusted Person row, with FIPS codes correctly padded
    to be of length 5 digits
    """
    # Deal with 15005 vs 15009 FIPS Code
    if state == '15':
        if county == '5':
            county = '9'
    # Ensure State FIPS are left padded
    if len(state) == 1:
        state = '0' + state
    # Ensure County FIPS are left padded
    if len(county) == 1:
        county = '00' + county
    elif len(county) == 2:
        county = '0' + county
    return state, county

def get_file_to_write_to(outputLocation, state, FIPS, seen, fileName):
    """ 
    Summary:
    Based on the FIPS code from Module 4, this function determines which
    file we should write our output for Module 5.
    
    Input Arguments:    
    outputLocation: Path to Module 5 output directory
    state: State which current row's person resides in
    FIPS: FIPS which current row's person resides in
    seen: A list containing the FIPS codes we have seen
    
    Output:
    A csv.writer object for the file we are writing to and an updated listing
    of all of the FIPS codes we have seen
    """
    # If we have seen this code before, it's an old file
    if FIPS in seen:
        # Read with a+ as there is no chance of mixing data and we want to append
        # to what is currently there
        out = open(outputLocation + state + '_' + FIPS + '_' + fileName + '_' + tempSuffix, 'a+', encoding='utf8')
        personWriter = csv.writer(out, delimiter=',', lineterminator='\n')
    else:
        # Read with w+ to ensure old data doesn't mix with new data
        out = open(outputLocation + state + '_' + FIPS + '_' + fileName + '_' + tempSuffix, 'w+', encoding='utf8')
        personWriter = csv.writer(out, delimiter=',', lineterminator='\n')
        # Give the file a header
        writeHeaders2(personWriter)
        # Add it to list  of seen so we don't write headers again
        seen.append(FIPS)
    return seen, personWriter

def construct_initial_trip_files(fileLocation, outputLocation, state, startTime):
    """ 
    Summary:
    This function takes in the Module4NN Trip files and writes every row as a
    node with geographic attributes from a specified trip based on the 
    activity pattern. 
    
    Ex. Activity Pattern 6
    Output: Row H, Row W, Row O, Row H
    
    Every node is marked as complete or not complete based on
    whether sufficient information exists to describe the node's trip sequence.
    For all nodes departing from an other or ending in an other trip, this 
    information does not exist, so 0 is marked. Otherwise, 1 is marked.
    
    Input Arguments:   
    fileLocaton: Path to Module 4 input directory
    outputLocation: Path to Module 5 output directory
    state: State which current row's person resides in
    startTime: Start time of Module 5, used for timing.
    
    Output:
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    Additionally, a file detailing all the nodes written as described above.
    """
    f = open(fileLocation, 'r')
    personReader = csv.reader(f, delimiter=',')
    trailingFIPS = ''
    seen = []
    count = -1
    nodeHold = dict()
    nodeCount = 0
    validPrev = ['S','H','W']
    validEnd = ['S','H','W','N']
    for person in personReader:
        if count == -1: 
            count+=1 
            continue      
        count+=1
        
        # Correct FIPS Codes
        person[0], person[1] = correct_FIPS(person[0],person[1])
        newCounty = person[0] + person[1]
        # Change output file if FIPS changes
        if newCounty != trailingFIPS:
            if trailingFIPS in nodeHold:
                nodeHold[trailingFIPS] += nodeCount
                nodeCount = 0
                nodeHold[newCounty] = nodeCount
            else:
                if trailingFIPS == '':
                    nodeCount = 0
                    nodeHold[newCounty] = nodeCount
                else:
                    nodeHold[trailingFIPS] += nodeCount
                    nodeCount = 0
                    nodeHold[newCounty] = nodeCount
            trailingFIPS = newCounty
            dictWriter = get_file_to_write_to(outputLocation, state, trailingFIPS, seen[:], 'Head')[1]
            seen, personWriter = get_file_to_write_to(outputLocation, state, trailingFIPS, seen, 'Pass0')
        
        dictWriter.writerow([count] + person[:5] + [person[8]] + [person[len(person)-1]])        
        # Get personal tours constructed for sorting
        personalTour = activityPattern.activityPattern(int(person[len(person) - 1]), person, count)
        for node in personalTour.activities:
            # Write any node that is not an NA node
            if 'NA' not in node[0]:
                isComplete = 0
                if len(node[5]) == 4:
                    node[5] = '0' + node[5]
                # No other trips needed, so we have everything we need to write this trip down
                if node[0] in validPrev and node[3] in validEnd:
                    isComplete = 1
                nodeCount +=1
                personWriter.writerow([node[0]] + [node[2]] + [node[3]] + 
                                  [node[4]] + [node[5]] + [node[6]] + 
                                  [node[7]] + [node[8]] + [node[9]] +
                                  [node[10]] + [node[11]] + [node[12]] + [isComplete])
        if count % 100000 == 0:
            print(str(count) + ' Residents Completed and taken this much time: ' + str(datetime.now()-startTime))

    f.close()
    medianRow = statistics.median(sorted([count for count in nodeHold.values()]))
    if medianRow == 0:
        medianRow = 500000
    return seen, medianRow

def construct_initial_files_splitter(outputLocation, state, seen, medianRow):
    totalFiles = []
    for FIPS in seen:
        f = open(outputLocation + state + '_' + FIPS + '_' + 'Pass0' + '_' + tempSuffix,'r+', encoding='utf8')
        FIPSFiles = split_csv(f,output_name_template= state + '_' + FIPS + '_' + tempSuffixNoFile + '_' + 'Pass0', 
                              row_limit = medianRow, output_path = outputLocation)
        totalFiles.append(FIPSFiles)
        f.close()
        try:
            os.remove(outputLocation + state + '_' + FIPS + '_' + 'Pass0' + '_' + tempSuffix)
        except:
            print('Unable to remove initial file @', FIPS,)
    return [item for sublist in totalFiles for item in sublist]

def split_csv(filehandler, output_name_template, delimiter=',', row_limit=10000, 
    output_path='.', keep_headers=True):
    """
    Splits a CSV file into multiple pieces.
    
    Arguments:
        `filehandler`: an open() object called on the file.
        `delimiter`: Delimiter used to separate entries. Comma used by default (.csv).
        `row_limit`: The number of rows you want in each output file. 10,000 by default.
        `output_name_template`: A %s-style template for the numbered output files by default.
        `output_path`: Where to write the output files.
        `keep_headers`: Whether or not to print the headers in each output file.
    Example usage:
    
        >> from toolbox import csv_splitter;
        >> csv_splitter.split(open('/home/ben/input.csv', 'r'));
    
    """
    # Construct reader from filehandler
    seenFiles = []
    reader = csv.reader(filehandler, delimiter=delimiter,lineterminator='\n')
    current_piece = 1
    current_out_path = os.path.join(output_path,output_name_template + '_' + str(current_piece) + '.csv')
    seenFiles.append(output_name_template + '_' + str(current_piece) + '.csv')
    o = open(current_out_path, 'w+', encoding='utf8')
    current_out_writer = csv.writer(o,delimiter=delimiter,lineterminator='\n')
    current_limit = row_limit
    count = 0
    if keep_headers:
        count = -1
    lineVec = []
    for r in reader:
        if count == -1:
            current_out_writer.writerow(r)
            count+=1
            continue
        if count - 1 > current_limit:
            if len(lineVec) == 0:
                lineVec.append((r[8],r[9]))
            else:
                valToConfirm = lineVec.pop()
                if valToConfirm == (r[8],r[9]):
                    lineVec.append((r[8],r[9]))
                    #print(len(lineVec))
                    current_out_writer.writerow(r)
                    continue
                else:
                    current_piece += 1
                    current_limit = row_limit * current_piece
                    current_out_path = os.path.join(output_path,output_name_template + '_' + str(current_piece) + '.csv')
                    o = open(current_out_path, 'w+', encoding='utf8')
                    seenFiles.append(output_name_template + '_' + str(current_piece) + '.csv')
                    current_out_writer = csv.writer(o,delimiter=delimiter,lineterminator='\n')
                    writeHeaders2(current_out_writer)
        current_out_writer.writerow(r)
        count+=1    
    return seenFiles

def sort_files_before_splitter(outputLocation, state, seen, iteration, inputFile, outputFile):
    """ 
    Summary:
    This function sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by County, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects. This sorting is done before splitting the files, so it operates on
    county-wide files, not split county files.
    
    Input Arguments:   
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Output:
    A sorted file as described above.
    """
    # If we're on iteration 1, we need to access the initial trip files, which
    # are named as 0. Otherwise, the name is based on the iteration number.
    past = iteration
    if iteration == '1':
        past = str(int(iteration)-1)
    for FIPS in seen:
        print("Sorting Before Splitter: ", FIPS, " on Iteration: ", iteration)
        reader = pd.read_csv(outputLocation + state + '_' + FIPS + '_' + inputFile + past + '_' + tempSuffix,
                 dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                          'Node Name': str, 'Node County': str, 'Node Lat': str, 'Node Lon': str, 
                          'Node Industry': str, 'XCoord': int, 'YCoord': int, 'Segment': int, 'Row': int})
        reader = reader.sort_values(by=['Node County','XCoord','YCoord','Node Successor','Node Type'], ascending=[True,True,True,True,True])
        reader.to_csv(outputLocation + state + '_' + FIPS + '_' + outputFile + iteration + '_' + tempSuffix, index=False, na_rep = 'NA')
    
def sort_files_before_pass(outputLocation, state, seen, iteration, outputFile):
    """ 
    Summary:
    This function sorts node files by County, XCoord, YCoord, Node Successor and Node
    Type prior to passing through the file to find the other trip locations. By
    sorting by County, then (X,Y) coords, we are able to minimize the number of
    times we need to read in new data and maximize reuse for the patronageWarehouse
    objects.
    
    Input Arguments:   
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Output:
    A sorted file as described above.
    """
    # If we're on iteration 1, we need to access the initial trip files, which
    # are named as 0. Otherwise, the name is based on the iteration number.
    updatedSeen = []
    numState = len(state)
    for file in seen:
        print("Sorting Before Pass: ", file, " on Iteration: ", iteration)
        reader = pd.read_csv(outputLocation + file,
                 dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                          'Node Name': str, 'Node County': str, 'Node Lat': str, 'Node Lon': str, 
                          'Node Industry': str, 'XCoord': int, 'YCoord': int, 'Segment': int, 'Row': int})
        reader = reader.sort_values(by=['Node County','XCoord','YCoord','Node Successor','Node Type'], ascending=[True,True,True,True,True])
        reader.to_csv(outputLocation + state + file[numState:(numState+18)] + '_' +
        outputFile + iteration + '_' + file[(numState+25):], index=False, na_rep = 'NA')
        updatedSeen.append(state + file[numState:numState+18] + '_' + outputFile + iteration + '_' + file[numState+25:])
    return updatedSeen

def pass_over_files(outputLocation, state, seen, iteration, countyNameData, numProcessors):
    pool = multiprocessing.Pool(numProcessors)    
    # Build task list
    tasks = []
    plotNum = 0
    numState = len(state)
    updatedSeen = []
    for file in seen:
        FIPS = file[numState+1:numState+6]
        plotNum += 1
        inFile = outputLocation + file
        outFile = outputLocation + state + file[numState:numState+18] + '_' + 'Pass' + iteration + '_' + file[numState+25:]
        tasks.append((inFile, outFile, countyNameData, FIPS[:2] , iteration, plotNum, FIPS))
        updatedSeen.append(state + file[numState:numState+18] + '_' + 'Pass' + iteration + '_' + file[numState+25:])
    
    
    results = [pool.apply_async(findOtherTrips.get_other_trip_parallel, t) for t in tasks]
    
    for result in results:
        num, currFIPS = result.get()
        print(num ," at ", currFIPS, " finished at ", datetime.now())
    
    pool.close()
    pool.join()
    return updatedSeen

def clean_files(outputLocation, state, seen, iteration):
    """ 
    Summary:
    This cleans out files from previous iterations that are no longer needed.
    
    Input Arguments:   
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Output:
    Removes files as shown below.
    """
    past = str(int(iteration)-1)
    numState = len(state)
    
    for file in seen:
        if iteration == '4':
            try:
                os.remove(outputLocation + file)
            except:
                print('Unable to remove file named: ', file)
        else:
            try:
                os.remove(outputLocation + state + file[numState:numState+18] + '_' + 'Sort' + iteration + '_' + file[numState+25:])
            except:
                print('Unable to remove SORT type folder for FIPS: ', file)
            try:
                os.remove(outputLocation + state + file[numState:numState+18] + '_' + 'Pass' + past + '_' + file[numState+25:])
            except:
                print('Unable to remove PASS type folder for FIPS: ', file)

def sort_files_after_pass(outputLocation, state, seen, iteration, outputFile):
    """ 
    Summary:
    This function sorts node files by Row and Segment after passing through the
    file to find the other type node locations. This allows us to quickly reconstruct
    trip files for the next iteration/final output in rebuild_trips().
    
    Input Arguments:   
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Output:
    A sorted file as described above.
    """
    updatedSeen = []
    numState = len(state)
    future = str(int(iteration)+1)
    for file in seen:
        print("Sorting After Pass: ", file, " on Iteration: ", iteration)
        reader = pd.read_csv(outputLocation + file,
                 dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                          'Node Name': str, 'Node County': str, 'Node Lat': str, 'Node Lon': str, 
                          'Node Industry': str, 'XCoord': int, 'YCoord': int, 'Segment': int, 'Row': int,
                          'IsComplete': str, 'D Node Name': str, 'D Node County': str, 'D Node Lat': str, 'D Node Lon': str, 
                          'D Node Industry': str, 'D XCoord': str, 'D YCoord': str})
        reader = reader.sort_values(by=['Row','Segment'], ascending=[True,True])
        reader.to_csv(outputLocation + state + file[numState:numState+18] + '_' +
        outputFile + future + '_' + file[numState+25:], index=False, na_rep = 'NA')
        updatedSeen.append(state + file[numState:numState+18] + '_' + outputFile + future + '_' + file[numState+25:])
    clean_files(outputLocation, state, seen, iteration)
    return updatedSeen


def rebuild_trips(outputLocation, state, seen, iteration):    
    """ 
    Summary:
    This function rebuilds the trip files by taking nodes sorted by Row and Segment
    to fill in O destination nodes. get_other_trips() writes out the destination
    node information, if found, in the 7 columns following the initial isComplete
    boolean column from the initial trip file. The data following this column is
    taken and filled in for subsequent nodes that were previously marked as NA
    due to issues with a lack of O destination node or uncertainty on the O 
    origin node.
    
    Input Arguments:   
    outputLocation: Path to files holding node information
    state: State which current row's person resides in
    seen: A list containing FIPS codes seen in the process of constructing
    the trips.
    iteration: Which iteration of passing we are on (1 or 2)
    
    Output:
    A file with newly gained information on the other type node destinations 
    now filled in.
    """
    updatedSeen = []
    numState = len(state)
    for file in seen:
        print('Rebuilding ',file, 'at iteration ',iteration)
        f = open(outputLocation + file, 'r+')
        personReader = csv.reader(f, delimiter = ',')
        o = open(outputLocation + state + file[numState:numState+18] + '_' + 'Pass' + iteration + '_' + file[numState+25:], 'w+', newline = '')
        personWriter = csv.writer(o, delimiter = ',')
        writeHeaders2(personWriter)
        updatedSeen.append(state + file[numState:numState+18] + '_' + 'Pass' + iteration + '_' + file[numState+25:])
        count = -1
        # Use trailing to get hold geographic attributes from previous node
        trailing = ''
        
        for line in personReader:
            if count == -1:
                count +=1
                continue
            count +=1
            # If it's incomplete, is an other-type node and isn't preceded
            # by an other type trip
            if line[12] == '0' and line[0] == 'O' and line[1] != 'O':
                line[3:10] = trailing
                if line[2] != 'O':
                    line[12] = '1'
            
            trailing = line[13:]
            personWriter.writerow(line[:13])
            
        f.close()
        o.close()
    return updatedSeen

def construct_row_personal_info_dict(FIPS, state, outputLocation):
    out = open(outputLocation + state + '_' + FIPS + '_' + 'Head' + '_' + tempSuffix, 'r', encoding='utf8')
    personReader = csv.reader(out, delimiter=',', lineterminator='\n')
    personDict = dict()
    count = -1
    for line in personReader:
        if count == -1:
            count +=1
            continue
        count += 1
        line[1], line[2] = correct_FIPS(line[1],line[2])
        personDict[int(line[0])] = line[1:]
    out.close()
    os.remove(outputLocation + state + '_' + FIPS + '_' + 'Head' + '_' + tempSuffix)
    return personDict

def merge_files(outputLocation, state, seen, FIPS):
    updatedSeen = []
    for code in FIPS:
        print('Merging FIPS code ', code)
        o = open(outputLocation + state + '_' + code + '_' + 'Merged' + '_' + tempSuffix, 'w+', encoding='utf8')
        personWriter = csv.writer(o, delimiter = ',',lineterminator='\n')
        writeHeaders2(personWriter)
        filesToMerge = [file for file in seen if code in file]
        for file in filesToMerge:
            f = open(outputLocation + file, 'r+', encoding='utf8')
            personReader = csv.reader(f, delimiter = ',',lineterminator='\n')
            count = -1
            for line in personReader:
                if count == -1:
                    count+=1
                    continue
                count+=1
                personWriter.writerow(line)
            f.close()
        o.close()
        reader = pd.read_csv(outputLocation + state + '_' + code + '_' + 'Merged' + '_' + tempSuffix,
                         dtype = {'Node Type': str, 'Node Predecessor': str, 'Node Successor': str,
                          'Node Name': str, 'Node County': str, 'Node Lat': str, 'Node Lon': str, 
                          'Node Industry': str, 'XCoord': int, 'YCoord': int, 'Segment': int, 'Row': int})
        reader = reader.sort_values(by=['Row','Segment'], ascending=[True,True])
        reader.to_csv(outputLocation + state + '_' + code + '_' + 'Merged' + '_' + tempSuffix, index=False, na_rep = 'NA')
        updatedSeen.append(state + '_' + code + '_' + 'Merged' + '_' + tempSuffix)
    return updatedSeen, seen
    
def rebuild_module_5_file(outputLocation, state, seen):    
    numState = len(state)
    for file in seen:
        FIPS = file[numState+1:numState+6]
        o = open(outputLocation + state + '_' + FIPS + '_' + outputFileNameSuffix, 'w+', newline = '')
        personWriter = csv.writer(o, delimiter = ',')
        f = open(outputLocation + file, 'r+')
        personReader = csv.reader(f, delimiter = ',')
        writeHeaders1(personWriter)
        rowDict = construct_row_personal_info_dict(FIPS, state, outputLocation)
        count = -1
        # Use trailing to get hold geographic attributes from previous node
        trailing = []
        currRow = ''
        nullNode = ['NA'] * 8
        numNodes = 7
        
        for line in personReader:
            if count == -1:
                count +=1
                continue
            count +=1
            
            if line[11] != currRow:
                for i in range(numNodes+1 - len(trailing)):
                    trailing.append(nullNode)
                finalRow = [item for sublist in trailing for item in sublist]
                if count != 1:
                    personWriter.writerow(finalRow)
                currRow = line[11]
                trailing = [rowDict[int(currRow)]]
                
            trailing.append(line[:8])
            
        f.close()
        o.close()

if __name__ == '__main__':
    # Handle command line options
    parser = argparse.ArgumentParser(description='Plot random data in parallel')
    parser.add_argument('-s', '--State', required=True,
                        help='The name of the state to be processed')
    parser.add_argument('--numProcessors', required=False, type=int, 
    					default=multiprocessing.cpu_count(),
    					help='Number of processors to use. ' + \
    					"Default for this machine is %d" % (multiprocessing.cpu_count(),) )
    args = parser.parse_args()
    
    if args.numProcessors < 1:
    	sys.exit('Number of processors to use must be greater than 0')

    # Module 4 Input Path
    fileLocation = rootFilePath + 'Module4/' + args.State + inputFileNameSuffix
    # Module 5 Output Path 
    outputLocation = rootFilePath + 'Module5/'

    startTime = datetime.now()
    print(args.State + " started at: " + str(startTime))
    
    FIPS, medianRow = construct_initial_trip_files(fileLocation, outputLocation, args.State, startTime)
    sort_files_before_splitter(outputLocation, args.State, FIPS, '0', 'Pass', 'Pass')
    seen = construct_initial_files_splitter(outputLocation, args.State, FIPS, medianRow)
    countyNameData = classDumpModule5.read_counties()
    print(seen)
    for i in range(1,3):
        
        current = str(i)
        future = str(i+1)
        
        print('Began sorting before passing on iteration: ', str(i), ' at', str(datetime.now()-startTime))
        seen = sort_files_before_pass(outputLocation, args.State, seen, current, 'Sort')
        print('Finished sorting before passing on iteration: ', str(i), ' at', str(datetime.now()-startTime))        
        seen = pass_over_files(outputLocation, args.State, seen, current, countyNameData, args.numProcessors)
        print('Finished passing over files on iteration: ', str(i), ' at', str(datetime.now()-startTime))    
        print('sorting')        
        seen = sort_files_after_pass(outputLocation, args.State, seen, current, 'Sort')       
        print('Finished sorting files after passing on iteration: ', str(i), ' at', str(datetime.now()-startTime))
        seen = rebuild_trips(outputLocation, args.State, seen, future)
        print('Finished iteration: ', str(i))
          
    clean_files(outputLocation, args.State, seen, '3')
    print(datetime.now()-startTime)
    newSeen, oldSeen = merge_files(outputLocation, args.State, seen, FIPS)
    print('final seen', newSeen, oldSeen)
    rebuild_module_5_file(outputLocation, args.State, newSeen)
    clean_files(outputLocation, args.State, newSeen + oldSeen, '4')
    
    print(args.State + " took: " + str(datetime.now() - startTime))
