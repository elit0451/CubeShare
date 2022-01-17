import ephem
import datetime

class FileHandler:

    # Ex: path = './data/sats.txt'
    def load_sat(self, path):
        sats_dict = {}

        with open(path) as file:
            for line in file:
                if line != '\n':  # Needed when having multiple sats TLEs
                    key = line.strip()
                    value = (file.readline().strip(), file.readline().strip())
                    sats_dict[key] = value
        sats_list = self.__get_sats_list(sats_dict)

        return sats_list

    # Ex: path = './data/stations.txt'
    def load_st(self, path):
        loc_list = []
        
        with open(path) as locations_file:

            # Skip Header row - columns names
            next(locations_file)

            for line in locations_file:
                data = line.split()
                name = data.pop(2)
                coordinates = data  # Get the rest of the elements
                location = self.__location_init(coordinates)
                loc_list.append(location)
        
        return loc_list

    # Ex: path = './data/s_tasks.txt'
    def load_loc(self, path):
        loc_list = []
        
        with open(path) as locations_file:

            # Skip Header row - columns names
            next(locations_file)

            for line in locations_file:
                data = line.split()
                booking_hours = data.pop(5)
                end_date = data.pop(4)
                start_date = data.pop(3)
                name = data.pop(2)
                coordinates = data  # Get the rest of the elements
                location = self.__location_init(coordinates)
                loc_list.append(task(name, start_date, end_date, booking_hours, location))
        
        return loc_list


    # _______________Private funcs_______________

    def __get_sats_list(self, sats_dict):
        sats_list = []
        for name in sats_dict:
            sat = self.__satellite_init(name, sats_dict[name])
            sats_list.append(sat)
        return sats_list

    # Initialize satellite object
    def __satellite_init(self, name, tle):
        # Set up the satellite
        sat_name = name
        tle_line1 = tle[0]
        tle_line2 = tle[1]

        sat = ephem.readtle(sat_name, tle_line1, tle_line2)
        return sat

    # Initialize location object
    def __location_init(self, coordinates):
        # Set up observer location
        loc = ephem.Observer()
        loc.lat = coordinates[0]  # +N
        loc.lon = coordinates[1]  # +E
        return loc

class task: 
    def __init__(self, name, start, end, booking_hours, loc_obj): 
        s_d_s = [int(i) for i in start.split('-')]
        e_d_s = [int(i) for i in end.split('-')]
        start_date = datetime.datetime(s_d_s[0], s_d_s[1], s_d_s[2], 0, 0, 0)
        end_date = datetime.datetime(e_d_s[0], e_d_s[1], e_d_s[2], 0, 0, 0)

        self.name = name
        self.start_date = start_date
        self.end_date = end_date
        self.booking_mins = int(booking_hours) * 60
        self.loc_obj = loc_obj