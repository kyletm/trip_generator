import sys
from ..utils import pixel

class Pattern:
    def __init__(self, trip_type, person, row):
        self.pattern = trip_type_to_pattern(trip_type)
        self.activities = make_activities(self.pattern, person, row)

def make_activities(pattern, person, row):
    """ Fills in the pattern/nodes in a person's activity pattern.
    
    As all details are known for Home, Work and School (H,W,S), everything
    related to these node types can be filled in. Details related to Other
    type nodes are left unfilled as information is still unknown.

    Input Arguments:
        pattern (list): An activity pattern for some traveller,
            generated from trip_type_to_pattern().
        person (list): The Module4NN row corresponding to the specific
            traveller. 
        row (int): The row number from Module4NN that corresponds to 
            this specific trip

    Output:
        activity_pattern (list): A filled activity pattern detailing the
            geographic and demographic attributes of every node visited 
            by a person throughout their activity pattern. Note that this
            activity pattern does not include the final trip home (node 8)
            for those activity patterns with a total of 7 nodes (e.g.
            Activity Patterns 19 and 20).
    """
    #TODO - Clean up this logic when time permits...
    num_activities = pattern[1]
    trip_tour = [[], [], [], [], [], [], [], []]
    for ind in range(num_activities + 1):
        trip_tour[ind] = [pattern[2][ind][0], ind]
        node_type = pattern[2][ind][0]
        'Assign Name, Lat, Lon'
        if node_type == 'H':
            name = 'Home'
            lat = float(person[6])
            lon = float(person[7])
            industry = 'NA'
            county = person[0] + person[1]
            x_pixel, y_pixel = pixel.find_pixel_coords(lat, lon)
        elif node_type == 'W':
            name = person[17]
            if name == 'International Destination for Work':
                lat = 'NA'
                lon = 'NA'
                industry = person[16]
                county = person[16]
                x_pixel, y_pixel = pixel.find_pixel_coords(0, 0)
            else:
                lat = float(person[28])
                lon = float(person[29])
                industry = (person[16])
                county = person[15]
                x_pixel, y_pixel = pixel.find_pixel_coords(lat, lon)
        elif node_type == 'S':
            name = person[35]
            if person[36] == 'UNKNOWN':
                lat = 0
                lon = 0
                x_pixel, y_pixel = pixel.find_pixel_coords(0, 0)
            else:
                try:
                    lat = float(person[36])
                    lon = float(person[37])
                    x_pixel, y_pixel = pixel.find_pixel_coords(lat, lon)
                except IndexError:
                    print('person', person)
                    sys.exit()
            industry = 'NA'
            county = (person[30])
        elif node_type == 'O':
            name = 'NA'
            lat = 'NA'
            lon = 'NA'
            industry = 'NA'
            county = trip_tour[ind-1][5]
            x_pixel, y_pixel = trip_tour[ind-1][9], trip_tour[ind-1][10]
        try:
            preceding = pattern[2][ind-1][0]
        except IndexError:
            preceding = 'NA'
        try:
            proceeding = pattern[2][ind+1][0]
        except IndexError:
            proceeding = 'NA'
        trip_tour[ind] = [pattern[2][ind][0], ind, preceding, proceeding, name,
                          county, lat, lon, industry, x_pixel, y_pixel, ind, row]
    for ind in range(num_activities + 1, 8):
        trip_tour[ind] = ['NA', 'NA', 'NA', 'NA', 'NA', 'NA',
                          'NA', 'NA', 'NA', 8233, -5376, ind, row]
    return [trip_tour[i] for i in range(7)]

def trip_type_to_pattern(trip_type):
    """Constructs an unfilled activity pattern for a trip type.
    
    Constructs a list of lists that forms the basic structure of every row
    written in Module 5. The first two elements list the trip type and the
    number of activities, and the last element (a list of lists) lists the 
    geographic and demographic attributes of every node visited throughout
    a person's daily travel.

    Input Arguments:
    trip_type (int): The trip type for a given travller.

    Output:
    activity_pattern (list): Unfilled activity pattern for a trip type.
    """
    #TODO - Find different data structure to hold this data...
    activities = [trip_type, [], [], [], [], [], [], [], []]
    if trip_type == -5 or trip_type == 0:
        activities = [trip_type, 0, [['H', 0], ['N', 1], ['N', 2], ['N', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 1:
        activities = [trip_type, 2, [['H', 0], ['W', 1], ['H', 2], ['N', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 2:
        activities = [trip_type, 2, [['H', 0], ['S', 1], ['H', 2], ['N', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 3:
        activities = [trip_type, 2, [['H', 0], ['O', 1], ['H', 2], ['N', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 4:
        activities = [trip_type, 3, [['H', 0], ['S', 1], ['W', 2], ['H', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 5:
        activities = [trip_type, 3, [['H', 0], ['W', 1], ['S', 2], ['H', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 6:
        activities = [trip_type, 3, [['H', 0], ['W', 1], ['O', 2], ['H', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 7:
        activities = [trip_type, 3, [['H', 0], ['S', 1], ['O', 2], ['H', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 8:
        activities = [trip_type, 3, [['H', 0], ['O', 1], ['O', 2], ['H', 3],
                                     ['N', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 9:
        activities = [trip_type, 4, [['H', 0], ['S', 1], ['W', 2], ['O', 3],
                                     ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 10:
        activities = [trip_type, 4, [['H', 0], ['W', 1], ['S', 2], ['O', 3],
                                     ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 11:
        activities = [trip_type, 4, [['H', 0], ['W', 1], ['H', 2], ['O', 3],
                                     ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 12:
        activities = [trip_type, 4, [['H', 0], ['S', 1], ['H', 2], ['O', 3],
                                     ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 13:
        activities = [trip_type, 4, [['H', 0], ['O', 1], ['H', 2], ['O', 3],
                                     ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 14:
        activities = [trip_type, 4, [['H', 0], ['W', 1], ['O', 2], ['W', 3],
                                     ['H', 4], ['N', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 15:
        activities = [trip_type, 5, [['H', 0], ['W', 1], ['O', 2], ['H', 3],
                                     ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 16:
        activities = [trip_type, 5, [['H', 0], ['S', 1], ['O', 2], ['H', 3],
                                     ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 17:
        activities = [trip_type, 5, [['H', 0], ['W', 1], ['H', 2], ['O', 3],
                                     ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 18:
        activities = [trip_type, 5, [['H', 0], ['S', 1], ['H', 2], ['O', 3],
                                     ['O', 4], ['H', 5], ['N', 6], ['N', 7]]]
    elif trip_type == 19:
        activities = [trip_type, 7, [['H', 0], ['W', 1], ['O', 2], ['H', 3],
                                     ['O', 4], ['H', 5], ['O', 6], ['H', 7]]]
    elif trip_type == 20:
        activities = [trip_type, 7, [['H', 0], ['S', 1], ['O', 2], ['H', 3],
                                     ['O', 4], ['H', 5], ['O', 6], ['H', 7]]]
    return activities
