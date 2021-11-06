import ephem
import datetime
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def main():
    sats_dict = {}
    stations_list = []

    # Read CubeSats TLEs
    #with open('orbits.txt') as file:
    with open('sats.txt') as file:
        for line in file:
            if line != '\n':
                key = line.strip()
                value = (file.readline().strip(), file.readline().strip())
                sats_dict[key] = value
        
    sats_list = get_sats_list(sats_dict)


    # Read Ground Stations coordinates
    with open('grStations.txt') as stations_file:

        # Skip Header row
        next(stations_file)

        for line in stations_file:
            coordinates = line.split()
            home_station = ground_st_init(coordinates)
            stations_list.append(home_station)

    # Set up the start and end times
    start_time = datetime.datetime(2015, 6, 4, 0, 0, 0)
    end_time = datetime.datetime(2015, 6, 10, 0, 0, 0)

    for sat in sats_list:
        for station in stations_list:
            passes = calculate_passes(start_time, end_time, station, sat)

    print_passes(passes)



def get_sats_list(sats_dict):
    sats_list = []
    for name in sats_dict:
        sat = satellite_init(name, sats_dict[name])
        sats_list.append(sat)
    return sats_list

def satellite_init(name, tle):
    # Set up the satellite
    sat_name = name
    tle_line1 = tle[0]
    tle_line2 = tle[1]

    sat = ephem.readtle(sat_name, tle_line1, tle_line2)
    return sat

def ground_st_init(coordinates):
    # Set up observer location
    home = ephem.Observer()
    home.lon = coordinates[0] # +E
    home.lat = coordinates[1] # +N
    home.elevation = 50 # Meters
    return home

def calculate_passes(start, end, ground_st, sat):
    # Set up the time step in seconds
    time_step = 60

    passes = []
    current_time = start

    # Calculate the passes
    while current_time < end:
        ground_st.date = current_time
        sat.compute(ground_st)
        passes.append((current_time, "{0}".format(sat.rise_time), "{0}".format(sat.transit_time), "{0}".format(sat.set_time)))
        current_time += datetime.timedelta(seconds = time_step)
    return passes

def print_passes(passes):
    data_frame = pd.DataFrame(passes, columns = ['Current', 'Rise', 'Transit', 'Set'])
    data_frame = data_frame.drop_duplicates(subset = ['Rise'], keep = 'first', inplace = False)
    print(data_frame)


if __name__ == "__main__":
    main()