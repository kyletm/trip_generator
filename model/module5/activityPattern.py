import sys 
import pixel

class activityPattern:
    def __init__(self, tripType, person, row):
        self.activityPattern = tripTypeToPattern(tripType)  
        self.activities = makeActivities(self.activityPattern, person, row)
        
def makeActivities(activities, person, row):
    """ 
    Summary:
    Fills in the activities/nodes in a person's activity pattern. As all details
    are known for Home, Work and School (H,W,S), everything can be filled in.
    Details related to Other type nodes are left unfilled as information is still
    unknown.
    
    Input Arguments:    
    activities: An activity pattern list, generated from tripTypeToPattern()
    person: The Module4NN row corresponding to the specific person making the
    trip
    row: The row number from Module4NN that corresponds to this specific trip
    
    Output:
    A filled activity pattern detailing the geographic and demographic attributes
    of every node visited by a person throughout their activity pattern.
    """
    numActivities = activities[1]
    temp = [[], [], [], [], [], [], [], []]
    for k in range(0, numActivities + 1):
        temp[k] = [activities[2][k][0], k ]
        stype = activities[2][k][0]
        'Assign Name, Lat, Lon'
        if stype == 'H':
            name = 'Home'
            lat = float(person[6])
            lon = float(person[7])
            indust = 'NA'
            county = person[0] + person[1]
            xPixel, yPixel = pixel.find_pixel_coords(lat,lon)
        elif stype == 'W':
            name = person[17]
            if name == 'International Destination for Work':
                lat = 'NA'
                lon = 'NA'
                indust = person[16]
                county = person[16]
                xPixel, yPixel = pixel.find_pixel_coords(0,0)
            else:
                lat = float(person[28])
                lon = float(person[29])
                indust = (person[16])
                county = person[15]
                xPixel, yPixel = pixel.find_pixel_coords(lat,lon)
        elif stype == 'S':
            name = person[35]
            if person[36] == 'UNKNOWN':
                lat = 0;
                lon = 0;
                xPixel, yPixel = pixel.find_pixel_coords(0,0)
            else:
                try:
                    lat = float(person[36])
                    lon = float(person[37])
                    xPixel, yPixel = pixel.find_pixel_coords(lat,lon)
                except:
                    print('person',person)
                    sys.exit()
            indust = 'NA'
            county = (person[30])
        elif stype == 'O':
            name = 'NA'
            lat = 'NA'
            lon = 'NA'
            indust = 'NA'
            county = temp[k-1][5]
            xPixel, yPixel = temp[k-1][9],temp[k-1][10]
        try:
            preceding = activities[2][k-1][0]
        except IndexError:
            preceding = 'NA'
        try:
            proceeding = activities[2][k+1][0]
        except IndexError:
            proceeding = 'NA' 
        temp[k] = [activities[2][k][0], k, preceding, proceeding, name, county, lat, lon, indust, xPixel, yPixel, k, row]
    for k in range(numActivities + 1, 8):
        temp[k] = ['NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 'NA', 8233, -5376, k, row]
    return [temp[0], temp[1], temp[2], temp[3], temp[4], temp[5], temp[6]]

def tripTypeToPattern(tripType):
    """ 
    Summary:
    Constructs a list of lists that forms the basic structure of every row
    written in Module 5. The first two elements list the trip type and the 
    number of activities, and the last element (a list of lists) is a basic
    holder element that lists the geographic and demographic attributes of 
    every node visited by throughout a person's daily travel.
    
    Input Arguments:    
    tripType: An integer detailing the trip type taken - see thesis for details
    specifiying which trip type corresponds to which activity pattern.
    
    Output:
    A list of lists detailing the nodes of the person's activity pattern.
    """
    activities = [tripType, [], [], [], [], [], [], [], []]
    if tripType == -5:
        activities = [tripType, 0, [['H', 0], ['N', 1], ['N', 2], ['N', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    if tripType == 0:
        activities = [tripType, 0, [['H', 0], ['N', 1], ['N', 2], ['N', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 1:
        activities = [tripType, 2, [['H', 0], ['W', 1], ['H', 2], ['N', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 2:
        activities = [tripType, 2, [['H', 0], ['S', 1], ['H', 2], ['N', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 3:
        activities = [tripType, 2, [['H', 0], ['O', 1], ['H', 2], ['N', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 4:
        activities = [tripType, 3, [['H', 0], ['S', 1], ['W', 2], ['H', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 5:
        activities = [tripType, 3, [['H', 0], ['W', 1], ['S', 2], ['H', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 6:
        activities = [tripType, 3, [['H', 0], ['W', 1], ['O', 2], ['H', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 7:
        activities = [tripType, 3, [['H', 0], ['S', 1], ['O', 2], ['H', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]] 
    elif tripType == 8:
        activities = [tripType, 3, [['H', 0], ['O', 1], ['O', 2], ['H', 3], ['N', 4], ['N', 5], ['N', 6], ['N', 7]]] 
    elif tripType == 9:
        activities = [tripType, 4, [['H', 0], ['S', 1], ['W', 2], ['O', 3], ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 10:
        activities = [tripType, 4, [['H', 0], ['W', 1], ['S', 2], ['O', 3], ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 11:
        activities = [tripType, 4, [['H', 0], ['W', 1], ['H', 2], ['O', 3], ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 12:
        activities = [tripType, 4, [['H', 0], ['S', 1], ['H', 2], ['O', 3], ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 13:
        activities = [tripType, 4, [['H', 0], ['O', 1], ['H', 2], ['O', 3], ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 14:
        activities = [tripType, 4, [['H', 0], ['W', 1], ['O', 2], ['W', 3], ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif tripType == 15:
        activities = [tripType, 5, [['H', 0], ['W', 1], ['O', 2], ['H', 3], ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif tripType == 16:
        activities = [tripType, 5, [['H', 0], ['S', 1], ['O', 2], ['H', 3], ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif tripType == 17:
        activities = [tripType, 5, [['H', 0], ['W', 1], ['H', 2], ['O', 3], ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif tripType == 18:
        activities = [tripType, 5, [['H', 0], ['S', 1], ['H', 2], ['O', 3], ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif tripType == 19:
        activities = [tripType, 7, [['H', 0], ['W', 1], ['O', 2], ['H', 3], ['O', 4], ['H', 5], ['O', 6], ['H', 7]]]
    elif tripType == 20:
        activities = [tripType, 7, [['H', 0], ['S', 1], ['O', 2], ['H', 3], ['O', 4], ['H', 5], ['O', 6], ['H', 7]]]
    return activities