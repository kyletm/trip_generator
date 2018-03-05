import random
import bisect
from ..module2 import industry
from ..utils import core, reading, writing, distance, pixel

NAISC_TO_INDUST = {11: 'agr', 21: 'mqo', 31: 'man', 32: 'man', 33: 'man',
                   42: 'wtr', 44: 'rtr', 45: 'rtr', 48: 'tra', 49: 'tra',
                   22: 'uti', 51: 'inf', 52: 'fin', 53: 'rer', 54: 'pro',
                   55: 'mgt', 56: 'adm', 61: 'edu', 62: 'hea', 71: 'art',
                   72: 'aco', 92: 'pub', 99: 'otr', 445: 'wow', 722: 'wow'}

class GeoAttributes:

    def __init__(self, x=None, y=None, fips=None, curr_node=None):
        self.fips = fips
        self.pix_coords = (x, y)
        self.curr_node = curr_node
        self.work_dist = None
        self.pat_county = None
        if self.fips is not None:
            self.pat_warehouse = PatronageWarehouse(fips)

    def update_attr(self, row, file):
        if (self.fips != row[4]
                or self.pix_coords != (int(row[8]), int(row[9]))
                or self.curr_node != row[0]):
            self.fips = row[4]
            self.pix_coords = (int(row[8]), int(row[9]))
            self.curr_node = row[0]
            self.pat_warehouse = PatronageWarehouse(self.fips)
            self.generate_new_dist()

    def generate_new_dist(self):
        """Generates distribution of other type trip locations for a pixel.

        The previous and future nodes of our current node are used to help deal with
        the geographic limitations of the W-O-W type trips.

        Note: Once we have patronage counts for a FIPS code, we can construct
        a CDF by industry and then save this for the FIPS code. While ideally
        we could force all trips to visit patronage places for one type of
        industry, this would be unrealistic as different counties have different
        industries (e.g. Manhattan, NY vs Mobile, AL).
        """
        index = None

        for count, pat_county in enumerate(self.pat_warehouse.counties[self.curr_node]):
            if self.fips == pat_county.fips:
                index = count
                break

        # Avoid doing this whenever possible due to high runtime cost...
        if index is None:
            self.pat_warehouse.counties[self.curr_node].append(PatronageCounty(self.fips))
            index = len(self.pat_warehouse.counties[self.curr_node]) - 1

        pat_county = self.pat_warehouse.counties[self.curr_node][index]
        self.work_dist = self.build_pat_place_distribution(pat_county)
        self.pat_county = pat_county

    def build_pat_place_distribution(self, pat_county):
        distances = {}
        # Note: Restrictons on geography are built into distance calculations
        x, y = self.pix_coords
        for naisc in pat_county.indust_dict.values():
            pat_places = naisc.pat_places
            reg_distances = []
            pat_pixels = [(float(pat_place[12]), pixel.find_pixel_coords(pat_place[15], pat_place[16]))
                          for pat_place in pat_places]
            if naisc.indust_type == 'otr':
                reg_distances = [ele[0] / distance.between_pixels(x, y, ele[1][0], ele[1][1])**2
                                 for ele in pat_pixels]
            else:
                reg_distances = [ele[0] / distance.between_pixels(x, y, ele[1][0], ele[1][1])
                                 for ele in pat_pixels]
            try:
                norm = sum(reg_distances)
                reg_distances = [j/norm for j in reg_distances]
            except ZeroDivisionError:
                pass
            distances[naisc.naisc] = reg_distances
        return distances

    def select_industry(self, predecessor, successor):
        split = random.random()
        industries = [self.pat_county.indust_dict[indust]
                      for indust in self.pat_county.indust_dict.keys()]
        patronage_counts = [naisc.patrons for naisc in industries]
        if (predecessor == 'W' and successor == 'W'
                and len(self.pat_county.indust_dict['otr'].pat_places) > 0):
            indust = 'otr'
        else:
            indust = industries[bisect.bisect(patronage_counts, split)].naisc
        return indust

    def update_patronage_dists(self):
        # TODO - Deprecated unless we decide to use sampling without replacement
        industries = [self.pat_county.indust_dict[indust]
                      for indust in self.pat_county.indust_dict.keys()]
        patronage_counts = [naisc.patrons for naisc in industries]
        for normalized_patron_count, naisc in zip(core.cdf(patronage_counts), industries):
            naisc.add_normalized_patrons(normalized_patron_count)

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
        indust = self.select_industry(predecessor, successor)
        pat_places = self.pat_county.indust_dict[indust].pat_places
        distance_dist = self.work_dist[indust]
        if sum(distance_dist) == 0:
            index = random.randint(0, len(distance_dist) - 1)
        else:
            weights = core.cdf(distance_dist)
            split = random.random()
            index = bisect.bisect(weights, split)
        selected_location = pat_places[index]
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
        self.counties = {'H': [], 'W': [], 'S': [], 'O': []}
        self.counties['H'].append(PatronageCounty(home_fips))

class Industry:

    def __init__(self, naisc, indust_type):
        self.indust_type = indust_type
        self.naisc = naisc
        self.patrons = 0
        self.pat_places = []

    def add_pat_place(self, pat_place, patrons):
        self.patrons += patrons
        self.pat_places.append(pat_place)

def parse_patron_num(patron_num):
    if len(patron_num) == 8:
        if patron_num[len(patron_num) - 3] == '+':
            patron_num = 10000
    else:
        patron_num = int(patron_num)
    return patron_num

class PatronageCounty:

    def __init__(self, fips):
        self.fips = str(fips)
        self.indust_dict = self.create_industry_lists()

    def create_industry_lists(self):
        indust_dict = {code: Industry(code, NAISC_TO_INDUST[code])
                       for code in NAISC_TO_INDUST}
        pat_places = industry.read_county_employment(self.fips)
        for pat_place in pat_places:
            if pat_place[9] == 'NA':
                extended_code = '99'
            else:
                extended_code = pat_place[9][0:3]

            indust_code = int(extended_code[0:2])
            if indust_code not in set(indust_dict.keys()):
                indust_code = 99
            extended_code = int(extended_code)
            patron_num = parse_patron_num(pat_place[12])
            indust_dict[indust_code].add_pat_place(pat_place, patron_num)
            if extended_code in (445, 722):
                indust_dict[extended_code].add_pat_place(pat_place, patron_num)
        return indust_dict

def write_rebuilt_headers(writer):
    writer.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor']
                    + ['Node Name'] + ['Node County'] + ['Node Lat'] + ['Node Lon']
                    + ['Node Industry'] + ['XCoord'] + ['YCoord'] + ['Segment']
                    + ['Row'] + ['IsComplete'] + ['D Node Name'] + ['D Node County']
                    + ['D Node Lat'] + ['D Node Lon'] + ['D Node Industry']
                    + ['D XCoord'] + ['D YCoord'])

def get_other_trip(input_file, output_file, iteration, cpu_num=None, fips=None):
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
        valid_prev = ('S', 'H', 'W')
    # Otherwise, we can handle every trip type
    else:
        valid_prev = ('S', 'H', 'W', 'O')
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
            if row[4] == 'NA':
                print('NA found')
                continue
            if row[0] in valid_prev and row[12] == '0' and row[2] == 'O':
                geo.update_attr(row, input_file)
                name, county_name, curr_state, lat, lon, indust = geo.select_location(row[1], row[2])
                # Lookup the county name
                try:
                    fips = state_county_dict[curr_state][county_name]
                except KeyError:
                    state_code = state_code_dict[curr_state]
                    fips = core.lookup_name(county_name, state_code, county_name_data)
                x_coord, y_coord = pixel.find_pixel_coords(lat, lon)
                writer.writerow([row[0]] + [row[1]] + [row[2]]
                                + [row[3]] + [row[4]] + [row[5]]
                                + [row[6]] + [row[7]] + [row[8]]
                                + [row[9]] + [row[10]] + [row[11]]
                                + [1] + [name] + [fips] + [lat] + [lon]
                                + [indust] + [x_coord] + [y_coord])
            else:
              # The trip wasn't generated, so we mark it as not complete and write
              # all geographic attributes as NA
                writer.writerow([row[0]] + [row[1]] + [row[2]]
                                + [row[3]] + [row[4]] + [row[5]]
                                + [row[6]] + [row[7]] + [row[8]]
                                + [row[9]] + [row[10]] + [row[11]]
                                + [row[12]] + ['NA'] + ['NA'] + ['NA']
                                + ['NA'] + ['NA'] + ['NA'] + ['NA'])
    if cpu_num is not None and fips is not None:
        return cpu_num, fips
