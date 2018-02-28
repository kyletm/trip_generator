from ..module2 import industry
from ..utils import core, reading, writing, distance, pixel
from . import classDumpModule5
import random
import bisect

class GeoAttributes:
    
    def __init__(self, x = None, y = None, fips = None, curr_node = None):
        self.fips = fips
        self.pix_coords = (x,y)
        self.curr_node = curr_node
        self.indus_dist = None
        self.work_dist = None
        self.sets = None
        self.pat_warehouse = PatronageWarehouse(fips)

    def update_attr(self, row):
        if self.fips != row[4]:
            self.fips = row[4]
            self.PatronageWarehouse = self.create_warehouse(row[4])
            self.generate_new_dist()
        elif self.pix_coords != (int(row[8]), int(row[9])):
            self.pix_coords = (int(row[8]), int(row[9]))
            self.generate_new_dist()
        elif self.currentNode != row[0]:
            self.currentNode = row[0]
            self.generate_new_dist() 
    
    def generate_new_dist(self):
        """ 
        Summary:
        This function generates a new trip distribution from a gixen pixel centroid,
        current node type and specific fips in geo, a GeoAttributes type object.
        The previous and future nodes of our current node are used to help deal with
        the geographic limitations of the W-O-W type trips. The code can be described
        as follows:
        
        1. We use the PatronageWarehouse attribute of the GeoAttributes object to hold
        our employment patronage data, and first check if we have already seen our specified
        fips county before within our node set of counties (H,S,W,O). 
        
        2.If we have already seen this fips code before, we can reuse the already
        generated data - if not, we need to read this data into memory. This isn't
        computationally cheap, so we want to avoid doing this when possible.
        
        3. Once we have our patronage counts for a fips code, we construct a CDF
        by industry and then save this for the fips county. Note: we can't go
        any further in the distribution saving process (e.g. we can't compute the 
        distance distribution for all businesses from our pixel across the same
        pixel) as we first select an industry and then select businesses from this
        industry. Selecting and holding an industry constant would lead to trip destinations
        that are not proportional to the true destinations. Constructing a trip destination
        for every possible business (e.g. across all industries) for this specific 
        pixel has an excessive computational cost and places trip distributions proportional
        to the number of patrons across all businesses, as opposed to the patronage
        across industries, then amongst industries in that business.
        
        4. Once these steps are complete, we save the distribution and return it 
        to select the other trip location.
        """
        home_county_patronage = self.PatronageWarehouse
        current = self.currentNode
        count = 0
        index = -1
        if current == 'H': 
            sets = home_county_patronage.home_counties
        elif current == 'S': 
            sets = home_county_patronage.school_counties
        elif current == 'W': 
            sets = home_county_patronage.work_counties
        else: 
            sets = home_county_patronage.other_counties
        # If we've seen this FIPS code before, grab its index from the PatronageWarehouse
        # so we can reuse it later
        #TODO - Investigate whether or not this is a bug...
        for j in sets:
            if self.fips == j.fips:
                index = count
                break
        # If we haven't seen this fips code before , read the data in
        if index == -1:
            if current == 'H':
                home_county_patronage.homeCounties.append(PatronageCounty(self.fips))
                index = len(home_county_patronage.homeCounties) - 1
                sets = home_county_patronage.homeCounties
            elif current == 'S':
                home_county_patronage.schoolCounties.append(PatronageCounty(self.fips))
                index = len(home_county_patronage.schoolCounties) - 1
                sets = home_county_patronage.schoolCounties
            elif current == 'W':
                home_county_patronage.workCounties.append(PatronageCounty(self.fips))
                index = len(home_county_patronage.workCounties) - 1
                sets = home_county_patronage.workCounties
            elif current == 'O':
                home_county_patronage.otherCounties.append(PatronageCounty(self.fips))
                index = len(home_county_patronage.otherCounties) - 1
                sets = home_county_patronage.otherCounties
        # Select our specific countyPatronage data
        countyPatronage = sets[index]
        # Construct a cdf detailing the industry weights for selection later
        industry_weights = core.cdf(countyPatronage.patronCounts)
        # Save the data into our GeoAttributes object
        distances = []
        # Note: Restrictons on geography are built into distance calculations
        x, y = self.pix_coords
        for idx in range(len(industry_weights)):
            lists = countyPatronage.industries[idx]
            reg_distances = []
            pat_pixels = [(float(emp[12]), pixel.find_pixel_coords(float(emp[15]), float(emp[16])))
                          for emp in lists]
            if idx == len(industry_weights)-1:
                reg_distances = [ele[0] / distance.between_pixels(x, y, ele[1][0], ele[1][1])**2
                                for ele in pat_pixels]
            else:
                reg_distances = [ele[0] / distance.between_pixels(x, y, ele[1][0], ele[1][1])
                                for ele in pat_pixels] 
            try:
                norm = sum(reg_distances)
                [j/norm for j in reg_distances]
            except ZeroDivisionError:
                pass
            distances.append(reg_distances)
        # Case: Every destination is on the origin, so we can't construct a cdf
        # In this case, we just randomly sample uniformly amongst the alternatives
    
        self.indus_dist = industry_weights
        self.work_dist = distances
        self.sets = countyPatronage
    
    def select_location(self, predecessor, successor):
        """ 
        Summary:
        This function generates the actual other trip location for any trip that ends
        in an other destination (e.g. W-O, S-O, H-O, O-O) using the saved distribution
        from the GeoAttributes object. Geographical assumptions are built into the
        trip selection process (e.g. for W-O-W trips) via the distribution construction.
        
        Input Arguments:   
        geo: A GeoAttributes object.
        predecessor, successor: The predecessor and successor nodes to our current node.
        
        Output:
        name: The name of the other trip location.
        county: The County Name (NOT THE fips CODE!) of the other trip location. Note: there is
        currently a (possible?) bug in the code or data where the name is returned
        as a None type object, so we have no information on what the fips code actually is.
        This data is recovered later in Module 6/7 by doing a lat,long > fips lookup.
        lat, lon: The lat, long coordinate pair of the destination.
        indust: The NAISC Code for the industry of the destination, if it exists.
        """
        # Case for W-O-W trips
        marker = False
        if predecessor == 'W' and successor == 'W': 
            marker = True
        split = random.random()
        # If not a W-O-W trip, select proportional to industry
        if marker == False:
            idx = bisect.bisect(self.indus_dist, split)
        # If it is a W-O-W trip, we select the last industry, which corresponds
        # to W-O-W trips
        else:
            idx = len(self.indust_dist)-1
            if len(self.sets.industries[idx]) == 0:
                idx = bisect.bisect(self.indust_dist, split)
        if self.sets.patronCounts[idx] > 5:
            self.sets.patronCounts[idx]-=1
        lists = self.sets.industries[idx]
        # Select the particular patronage location
        allDistances = self.work_dist[idx]
        # Construct distribution    
        if sum(allDistances) == 0:
            index = random.randint(0, len(allDistances) - 1)
        # If every destination is NOT on the origin, we sample according to distribution
        else:
            weights = core.cdf(allDistances)
            split = random.random()
            index = bisect.bisect(weights, split)
        try: 
            int(self.sets.industries[idx][index][12])
        except:
            self.sets.industries[idx][index][12] = float(self.sets.industries[idx][index][12])
        if int(self.sets.industries[idx][index][12]) > 1:
            self.sets.industries[idx][index][12] = int(self.sets.industries[idx][index][12]) - 1
        selected_location = lists[index]
        # Get other trip information and return it
        name = selected_location[0]
        county = selected_location[5].replace('.', '')
        lat = float(selected_location[len(selected_location) - 2])
        lon = float(selected_location[len(selected_location) - 1].strip('\n'))
        indust = selected_location[9][0:2]
        state = selected_location[3]
        return name, county, state, lat, lon, indust  

class PatronageWarehouse:
    # Holder for PatronageCounty objects, allows us to reuse data
    def __init__(self, home_fips):
        self.home_counties = []
        self.work_counties = []  
        self.school_counties = []
        self.other_counties = []
        self.home_counties.append(PatronageCounty(fips))

#TODO - Fix the design of this class...
class PatronageCounty:
    
    def __init__(self, fips):
        self.data = industry.read_county_employment(fips)
        self.fips = str(fips)
        self.industries = []
        self.patronCounts = []
        self.create_industryLists()
        self.distributions = []
        self.spots = []

    'Partition Employers/Patrons into Industries'
    def create_industryLists(self):
        agr = []; mqo = []; con = []; man = []; wtr = []; rtr = []
        tra = []; uti = []; inf = []; fin = []; rer = []; pro = []
        mgt = []; adm = []; edu = []; hea = []; art = []; aco = []
        otr = []; pub = []; wow = []
        agrCount = 0; mqoCount = 0; conCount = 0; manCount = 0; wtrCount = 0;
        rtrCount = 0; traCount = 0; utiCount = 0; infCount = 0; finCount = 0;
        rerCount = 0; proCount = 0; mgtCount = 0; admCount = 0; eduCount = 0;
        heaCount = 0; artCount = 0; acoCount = 0; otrCount = 0; pubCount = 0;
        wowCount = 0
        for j in self.data:
            if j[9] == 'NA': fullCode = '99'
            else: fullCode = j[9][0:3]
            
            code = int(fullCode[0:2])
            fullCode = int(fullCode)
            'Deal With Scientific Notation'
            number = (j[12])
            if len(number) == 8:
                if number[len(number) - 3] == '+': 
                    number = 10000
            else:
                number = int(j[12])
            if (code == 11): agr.append(j); agrCount+=number
            elif (code == 21): mqo.append(j); mqoCount+=number
            elif (code == 23): con.append(j); conCount+=number
            elif (code in [31, 32, 33]): man.append(j); manCount+=number
            elif (code == 42): wtr.append(j); wtrCount+=number
            elif (code in [44, 45]): rtr.append(j); rtrCount+=number
            elif (code in [48, 49]): tra.append(j); traCount+=number
            elif (code == 22): uti.append(j); utiCount+=number
            elif (code == 51): inf.append(j); infCount+=number
            elif (code == 52): fin.append(j); finCount+=number
            elif (code == 53): rer.append(j); rerCount+=number
            elif (code == 54): pro.append(j); proCount+=number
            elif (code == 55): mgt.append(j); mgtCount+=number
            elif (code == 56): adm.append(j); admCount+=number
            elif (code == 61): edu.append(j); eduCount+=number
            elif (code == 62): hea.append(j); heaCount+=number
            elif (code == 71): art.append(j); artCount+=number
            elif (code == 72): aco.append(j); acoCount+=number
            elif (code == 81): otr.append(j); otrCount+=number
            elif (code == 92): pub.append(j); pubCount+=number
            else: otr.append(j); otrCount+=number
            
            if (fullCode == 445 or fullCode == 722): wow.append(j); wowCount+=number
                
        self.industries = [agr, mqo, con, man, wtr, rtr, tra, uti,
                           inf, fin, rer, pro, mgt, adm, edu, hea,
                           art, aco, otr, pub, wow]     
        self.patronCounts = [int(agrCount), int(mqoCount), int(conCount), int(manCount), wtrCount, rtrCount, traCount, utiCount,
                             infCount, finCount, rerCount, proCount, mgtCount, admCount, eduCount, heaCount,
                             int(artCount), int(acoCount), otrCount, pubCount, wowCount]

def write_rebuilt_headers(writer):
    writer.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor']
                    + ['Node Name'] + ['Node County'] + ['Node Lat'] + ['Node Lon']
                    + ['Node Industry'] + ['XCoord'] + ['YCoord'] + ['Segment']
                    + ['Row'] + ['IsComplete'] + ['D Node Name'] + ['D Node County']
                    + ['D Node Lat'] + ['D Node Lon'] + ['D Node Industry']
                    + ['D XCoord'] + ['D YCoord'])
    
def get_other_trip(input_file, output_file, state, iteration, cpu_num=None, fips=None):
    """ 
    Summary:
    This function gets the other trips for a given fips file from Module 5 
    (handled via reader) and serves as the 'executive' function. 
    Trips are generated via function calls and written to the writer 
    object. All trips from reader are written to the writer object.
    If there is no trip generated, NA values are filled in detailing the geographic
    attributes of the node and the boolean isComplete column is marked as 0. 
    If there is a trip generated, we write in the geographic attributes of the
    trip and the boolean isComplete column is marked as 1.
    
    Input Arguments:   
    reader: A csv.reader type object that we read from.
    writer: A csv.writer type object that we write to.
    state: The state name.
    iteration: Which pass we are on (first or second), which is essential in determing
    the trip type we can examine. We can't look at O-O types in the first iteration
    as no O origins have been generated, but we can in the second.
    
    Output:
    A writer object with all of the nodes detailed whether or not they
    exist.
    """
    # If this is our first iteration, we have no other trips generated yet, so
    # we can't handle O-O type trips, so ignore these when they come up
    if iteration == '1':
        valid_prev = ('S','H','W')
    # Otherwise, we can handle every trip type
    else:
        valid_prev = ('S','H','W','O')
    # Initialize GeoAttributes
    county_name_data = core.read_counties()
    state_county_dict = core.state_county_dict()
    state_code_dict = core.state_code_dict()
    with open(input_file) as read, open(output_file, 'w+') as write:
        reader = reading.csv_reader(read)
        writer = writing.csv_writer(write)
        next(reader)
        write_rebuilt_headers(writer)
        geo = GeoAttributes()
        for row in reader:
            # If our node is a valid type (i.e. a valid previous destination to
            # and other type origin), then we examine it
            if row[4] == 'NA':
                print('NA found')
                continue
            if row[0] in valid_prev and row[12] == '0' and row[2] == 'O':
                geo.update_attr(row)
                # Select new location based off of our current pixel/node/fips
                name, county_name, curr_state, lat, lon, indust = geo.select_location(row[1], row[2])
                # Lookup the county name
                try:
                    fips = state_county_dict[curr_state][county_name]
                except KeyError:
                    state_code = state_code_dict[curr_state]
                    fips = classDumpModule5.lookup_name(county_name, state_code, county_name_data)
                # Get x,y pixel coords
                x, y = pixel.find_pixel_coords(lat, lon)
                # Write to writer - note that we marked the trip as Complete,
                # so row[12], which is 0, is replaced with a 1 to mark this
                writer.writerow([row[0]] + [row[1]] + [row[2]] + 
                  [row[3]] + [row[4]] + [row[5]] + 
                  [row[6]] + [row[7]] + [row[8]] +
                  [row[9]] + [row[10]] + [row[11]] + [1] + [name] + [fips] +
                  [lat] + [lon] + [indust] + [x] + [y])
            else:
              # The trip wasn't generated, so we mark it as not complete and write
              # all geographic attributes as NA
                writer.writerow([row[0]] + [row[1]] + [row[2]] + 
                      [row[3]] + [row[4]] + [row[5]] + 
                      [row[6]] + [row[7]] + [row[8]] +
                      [row[9]] + [row[10]] + [row[11]] + [row[12]] + 
                      ['NA'] + ['NA'] + ['NA'] + ['NA'] + ['NA'] +
                      ['NA'] + ['NA'])
    if cpu_num is not None and fips is not None:
            return cpu_num, fips
