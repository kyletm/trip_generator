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
    """Provides access to other-type trip distributions based on geographic attributes.

    Geographic attributes define the other type trip distribution we can
    sample from. To reduce I/O and other operations that come with generating
    a new other type trip distribution, we try to reuse the distribution
    whenever possible. However, if we have a change in location (e.g. pixel
    coordinates) of the traveller, then we must also change the distribution
    (as it is dependent on the location of the traveller).

    Attributes:
        fips (str): FIPS code associated with current distribution.
        pix_coords (tuple): Pixel Coords (X, Y) associated with current
            distribution.
        pat_place_dist (dict): Distribution of patronage places to pixel
            by NAISC industry, where each key is an NAISC industry (NAISC code)
            and value a normalized distribution (essentially the CDF) for
            sampling.
        pat_county (PatronageCounty): Current patronage county, used for
            performing operations on all data associated with distribution
            generation for a FIPS code.
        pat_warehouse (PatronageWarehouse): Used to store PatronageCounty
            objects to reduce I/O operations.
    """

    def __init__(self, x=None, y=None, fips=None, curr_node=None):
        """See class docstring"""
        self.fips = fips
        self.pix_coords = (x, y)
        self.curr_node = curr_node
        self.pat_place_dist = None
        self.pat_county = None
        if self.fips is not None:
            self.pat_warehouse = PatronageWarehouse(fips)

    def update_attr(self, row):
        """Defines conditions for when a new generation must be generated

        If FIPS code changes, then a new Patronage County object needs
        to be generated.

        If pixel changes, then a new distribution must be created centered
        on this pixel.

        If origin node changes, then a new Patronage County object is
        created. This was used used to reduce the amount of lookup for
        patronage counties when generating a new distribution but may
        represent a poor design flaw in the code.

        Inputs:
            row (list): Traveller row that distribution for other type trip
                is being generated off of.
        """

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
        self.pat_place_dist = self.build_pat_place_distribution(pat_county)
        self.pat_county = pat_county

    def build_pat_place_distribution(self, pat_county):
        """Builds patronage place distributions by NAISC industry

        Note that distributions are based around simplified pixel-to-pixel
        cartesian distance to calculations which provide a "good enough"
        distance approximation for the purposes of distribution generation.

        Inputs:
            pat_county (PatronageCounty): Current patronage county, used for
                performing operations on all data associated with distribution
                generation for a FIPS code.
        Returns:
            pat_place_dist (dict): Distribution of patronage places to pixel
                by NAISC industry, where each key is an NAISC industry
                (NAISC code) and value a normalized distribution (essentially
                the CDF) for sampling.
        """
        dist = {}
        # Note: Restrictons on geography are built into distance calculations
        x, y = self.pix_coords
        for naisc in pat_county.indust_dict.values():
            pat_places = naisc.pat_places
            normalized_dist = []
            pat_pixels = [(float(pat_place[12]), pixel.find_pixel_coords(pat_place[15], pat_place[16]))
                          for pat_place in pat_places]
            if naisc.indust_type == 'otr':
                normalized_dist = [ele[0] / distance.between_pixels(x, y, ele[1][0], ele[1][1])**2
                                   for ele in pat_pixels]
            else:
                normalized_dist = [ele[0] / distance.between_pixels(x, y, ele[1][0], ele[1][1])
                                   for ele in pat_pixels]
            try:
                norm = sum(normalized_dist)
                normalized_dist = [j/norm for j in normalized_dist]
            except ZeroDivisionError:
                pass
            dist[naisc.naisc] = normalized_dist
        return dist

    def select_industry(self, predecessor, successor):
        """Selects NAISC industry based on patronage counts for all NAISC
        industries in a county.

        Note that patronage counts here (and elsewhere) refer to the number
        of patrons (i.e. customers) a business gets on a typical day.

        Note for predecessor and successor, given the example:

        H-W-O-W-O-H

        and that we are looking to determine the NAISC industry for a trip
        on the first node (that is, the one between W and W), the predecessor
        to this trip is W and the successor is W.

        Inputs:
            predecessor (str): Arrival node for trip preceding this trip.
            successor (str): Arrival node for the trip after this trip.

        Returns:
            indust (int): Selected NAISC Industry code.
        """
        split = random.random()
        industries = [self.pat_county.indust_dict[indust]
                      for indust in self.pat_county.indust_dict.keys()]
        patronage_counts = [naisc.patrons for naisc in industries]
        if (predecessor == 'W' and successor == 'W'
                and self.pat_county.indust_dict['otr'].pat_places):
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
        """Selects physical location for O type trips from a distribution.

        Inputs:
            predecessor (str): Arrival node for trip preceding this trip.
            successor (str): Arrival node for the trip after this trip.

        Output:
            name (str): Name of the destination.
            county (str): County name of the other trip location.
            lat, lon (float): Lat, lon coordinate pair of the destination.
            indust (int): NAISC Code for the industry of the destination.
            state (int): Name of the U.S. state that the destination is in.
        """
        indust = self.select_industry(predecessor, successor)
        pat_places = self.pat_county.indust_dict[indust].pat_places
        distance_dist = self.pat_place_dist[indust]
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
    """Saves access to Patronage County objects for later reuse.

    Note: One additional approach might be to define a dictionary indexed
    by FIPS code for Patronage Counties and do one-hit search through
    that instead of a list?
    """
    def __init__(self, home_fips):
        """Initializes Patronage Warehouse object

        Inputs:
            home_fips (str): FIPS associated with H type node.
        """
        self.counties = {'H': [], 'W': [], 'S': [], 'O': []}
        self.counties['H'].append(PatronageCounty(home_fips))

class Industry:
    """Holds all patronage places associated with an NAISC code for a county.

    Attributes:
        indust_type (str): NAISC industry abbrevation.
        naisc (int): NAISC industry code.
        patrons (int): Patrons associated with industry in a county.
        pat_places (list): Elements are lists providing information
            about patronage places (e.g. employer locations) associated
            with that industry.
    """
    def __init__(self, naisc, indust_type):
        """Initializes Industry class

        Inputs:
            naisc (int): NAISC industry code.
            indust_type (str): NAISC industry abbreviation.
        """
        self.indust_type = indust_type
        self.naisc = naisc
        self.patrons = 0
        self.pat_places = []

    def add_pat_place(self, pat_place, patrons):
        """Adds patronage place to specific industry

        Inputs:
            pat_place (list): Patronage place, elements provide information
                describing the physical location and other attributes
                of the patronage place.
            patrons (int): Number of patrons that visit the place on an
                average day.
        """
        self.patrons += patrons
        self.pat_places.append(pat_place)

def parse_patron_num(patron_num):
    """Parses string representation of patron number.

    Deals with excessively high patronage numbers by limiting the max
    patronage number for a patronage place to be 10000.

    Inputs:
        patron_num (str): NAISC patron count for a patronage place.

    Returns:
        patron_num (int): NAISC patron count for a patronage place.
    """
    if len(patron_num) == 8:
        if patron_num[len(patron_num) - 3] == '+':
            patron_num = 10000
    else:
        patron_num = int(patron_num)
    return patron_num

class PatronageCounty:
    """Provides access to all NAISC Industries associated with a county.

    Attributes:
        fips (str): FIPS code associated with a county.
        indust_dict (dict): Key is NAISC code, value is Industry() associated
            with that code.
    """

    def __init__(self, fips):
        """See class docstring"""
        self.fips = str(fips)
        self.indust_dict = self.create_industry_dict()

    def create_industry_dict(self):
        """Creates industry dictionary for Patronage County

        Returns:
            indust_dict (dict): Key is NAISC code, value is Industry() associated
                with that code.
        """
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
    """Writes trip headers for processed trip files (i.e. Pass trip files)

    Inputs:
        writer (csv.writer): Writer for processed trip files.
    """
    writer.writerow(['Node Type'] + ['Node Predecessor'] + ['Node Successor']
                    + ['Node Name'] + ['Node County'] + ['Node Lat'] + ['Node Lon']
                    + ['Node Industry'] + ['XCoord'] + ['YCoord'] + ['Segment']
                    + ['Row'] + ['IsComplete'] + ['D Node Name'] + ['D Node County']
                    + ['D Node Lat'] + ['D Node Lon'] + ['D Node Industry']
                    + ['D XCoord'] + ['D YCoord'])

def get_other_trip(input_file, output_file, iteration, cpu_num=None, fips=None):
    """Finds all valid other trips for a given file of trip nodes.

    Supports both serial and parallel processing, this function can be called
    on partitions of the original trip file or the trip file itself.

    Note: If a trip is not processed because the origin is unknown, then
    it gets marked as incomplete (0) in the final column, otherwise it
    is marked as complete.

    Inputs:
        input_file (str): Input file path for Sort type file.
        output_file (str): Output file path for Pass type file.
        iteration (str): Current iteration of processing we are on.
        cpu_num (str): CPU Process assigned to this input file.
        fips (str): FIPS code that this file piece belongs to.
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
                geo.update_attr(row)
                name, county_name, curr_state, lat, lon, indust = geo.select_location(row[1], row[2])
                row[-1] = 1
                # Lookup the county name
                try:
                    fips = state_county_dict[curr_state][county_name]
                except KeyError:
                    state_code = state_code_dict[curr_state]
                    fips = core.lookup_name(county_name, state_code, county_name_data)
                x_coord, y_coord = pixel.find_pixel_coords(lat, lon)
                writer.writerow([row[i] for i in range(13)]
                                + [name] + [fips] + [lat] + [lon]
                                + [indust] + [x_coord] + [y_coord])
            else:
              # The trip wasn't generated, so we mark it as not complete and write
              # all geographic attributes as NA
                writer.writerow([row[i] for i in range(13)] + ['NA']*6)
    if cpu_num is not None and fips is not None:
        return cpu_num, fips
