import ephem
import datetime
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Set up observer location
home = ephem.Observer()
home.lon = '-1.292066'   # +E
home.lat = '54.555849'      # +N
home.elevation = 50 # meters

# Set up the satellite
sat_name = 'ALOSAT 1'
tle_line1 = '1 99997U          16033.50000000 -.00000000  00000-0  00000-0 0 00005'
tle_line2 = '2 99997 045.0363 000.0698 0005345 187.7360 172.2151 15.39232735000018'
sat = ephem.readtle(sat_name, tle_line1, tle_line2)

# Set up the start and end times
start_time = datetime.datetime(2015, 6, 4, 0, 0, 0)
end_time = datetime.datetime(2015, 6, 10, 0, 0, 0)

# Set up the time step in seconds
time_step = 60

# Calculate the passes
passes = []
current_time = start_time
while current_time < end_time:
    home.date = current_time
    sat.compute(home)
    passes.append((current_time, "{0}".format(sat.rise_time), "{0}".format(sat.transit_time), "{0}".format(sat.set_time)))
    current_time += datetime.timedelta(seconds=time_step)

#print(passes)
output=[]
# Print the passes
for rise_time, transit_time,  set_time, set in passes:
    output.append('Current: {0} Rise: {1} Transit: {2} Set: {3}'.format(rise_time, transit_time, set_time, set))
output_final=[]

df = pd.DataFrame(passes, columns=['Current', 'Rise', 'Transit', 'set'])
df = df.drop_duplicates(subset=['Rise'], keep='first', inplace=False)
print(df)
'''
def unique_string(list_of_string):
    unique_string = []
    for i in list_of_string:
        if i[43:50] not in unique_string:
            unique_string.append(i[43:50])
    return unique_string
'''

'''
for i in output:
    if i[43:50] not in output_final:
        output_final.append(i)
print(output_final)
'''
'''
def unique_rise_time_3(tuples):
    unique_list = []
    for i in range(len(tuples)):
        print(tuples[i])

        if tuples[i][1] not in unique_list:
            unique_list.append(tuples[i])
    print(unique_list)


unique_rise_time_3(passes)


def find_unique_tuples(lst):
    """
    >>> find_unique_tuples([(1,2),(1,2),(1,3)])
    [(1, 2), (1, 3)]
    >>> find_unique_tuples([(1,2),(1,2),(1,2)])
    []
    """
    unique_tuples = []
    for tup in lst:
        if lst.count(tup) == 1:
            unique_tuples.append(tup)
    return unique_tuples


(datetime.datetime(2015, 6, 4, 23, 52), 42158.67791268547, 42158.68087956676, 42158.68384436306)
(datetime.datetime(2015, 6, 4, 23, 53), 42158.677912684914, 42158.680879566295, 42158.68384436267)
(datetime.datetime(2015, 6, 4, 23, 54), 42158.67791268443, 42158.680879569394, 42158.68384436937)
(datetime.datetime(2015, 6, 4, 23, 55), 42158.67791268399, 42158.680879569125, 42158.68384436926)
(datetime.datetime(2015, 6, 4, 23, 56), 42158.677912683626, 42158.680879581465, 42158.68384439428)
(datetime.datetime(2015, 6, 4, 23, 57), 42158.67791268332, 42158.68087957764, 42158.68384438695)
(datetime.datetime(2015, 6, 4, 23, 58), 42158.67791268287, 42158.68087957433, 42158.683844380794)
(datetime.datetime(2015, 6, 4, 23, 59), 42158.677912682775, 42158.680879571766, 42158.683844375744)
'Current: 2015-06-04 23:58:00 Rise: 2015/6/5 04:16:12 T
'''

