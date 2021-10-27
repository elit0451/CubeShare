import ephem
import datetime
import math
import numpy as np
import matplotlib.pyplot as plt

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
start_time = datetime.datetime(2015, 6, 1, 0, 0, 0)
end_time = datetime.datetime(2015, 6, 2, 0, 0, 0)

# Set up the time step in seconds
time_step = 60

# Calculate the passes
passes = []
current_time = start_time
while current_time < end_time:
    home.date = current_time
    sat.compute(home)
    passes.append((current_time, sat.rise_time, sat.transit_time, sat.set_time))
    current_time += datetime.timedelta(seconds=time_step)

#print(passes)

# Print the passes
for rise_time, transit_time,  set_time, set in passes:
    print('Rise: {0} Transit: {1} Set: {2}'.format(rise_time, transit_time, set_time, set))
'''

# Plot the passes
rise_time, transit_time, set_time, set = zip(*passes)

plt.plot(rise_time, np.repeat(0, len(rise_time)), 'bo',
         transit_time, np.repeat(1, len(transit_time)), 'go',
         set_time, np.repeat(2, len(set_time)), 'ro')
plt.gca().set_ylim(-0.5, 2.5)
plt.show()
'''

