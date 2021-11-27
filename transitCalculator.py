import ephem
import datetime
import numpy as np
import pandas as pd
from fileHandler import FileHandler

class TransitCalculator:
    _sats_list = []
    _stations_list = []
    _tasks_loc_list = []

    def prepare(self):
        # Read CubeSats TLEs
        self._sats_list = FileHandler().load_sat('./data/sats.txt') # For more orbits use '../data/orbits.txt'

        # Read Ground Stations coordinates
        self._stations_list = FileHandler().load_st('./data/stations.txt') # For more gr station locations use '../data/grStations.txt'

        # Read Task Location coordinates
        self._tasks_loc_list = FileHandler().load_loc('./data/s_tasks.txt')

    # To work with more satellites than the first one from the list (self._sats_list[0]), modify this func to also receive the amount of sats
    def calculate(self, st_amount, task_amount):
        total_st_passes = []
        total_loc_passes = []

        # Work with only 1 satellite (the first one from the list)
        sat = self._sats_list[0]

        # Needed for the ground stations passes calculations - this approach decreases the computation complexity
        earliest_start = min(task.start_date for task in self._tasks_loc_list)
        latest_end = max(task.end_date for task in self._tasks_loc_list)

        # Calculate passes above ground stations
        i = 0
        while i < st_amount:
            passes_station = self.__calculate_passes(earliest_start, latest_end, self._stations_list[i], sat, True)
            total_st_passes.append(passes_station)
            i += 1

        # Calculate passes above tasks
        for location in self._tasks_loc_list:
            start_time = location.start_date
            end_time = location.end_date
            passes_location = self.__calculate_passes(start_time, end_time, location.loc_obj, sat, False)
            total_loc_passes.append(passes_location)

        all_passes = self.__gather_passes(total_st_passes, total_loc_passes, task_amount)

        self.__process_passes(all_passes, st_amount, task_amount)


    def __calculate_passes(self, start, end, loc, sat, is_station):
        # Set up the time step in seconds
        time_step = 60
        loc_Type = 'Home' if is_station else 'Task'
        passes = []
        current_time = start

        # Calculate the passes
        while current_time < end:
            loc.date = current_time
            sat.compute(loc)
            rt = ephem.localtime(sat.rise_time).strftime("%d/%m/%Y %X")
            tt = ephem.localtime(sat.transit_time).strftime("%d/%m/%Y %X")
            st = ephem.localtime(sat.set_time).strftime("%d/%m/%Y %X")
            passes.append((current_time.strftime("%d/%m/%Y %X"), rt, tt, st, loc_Type))
            current_time += datetime.timedelta(seconds=time_step)
        return passes

    # Combine data frames
    def __gather_passes(self, stations_passes, locations_passes, task_amount):
        small_st_dfs = []
        small_loc_dfs = []

        # Gather all stations passes
        for st_passes in stations_passes:
            data_frame_st = pd.DataFrame(st_passes, columns=['Current', 'Rise', 'Transit', 'Set', 'Type'])

            # Commenting out as we don't need to calculate that
            # Copy without reference
            #df_st = data_frame_st.copy()
            #df_st['Rise'] = pd.to_datetime(df_st['Rise'], format="%d/%m/%Y %X")
            #df_st['Set'] = pd.to_datetime(df_st['Set'], format="%d/%m/%Y %X")
            #df_st['Difference'] = df_st['Set'].sub(df_st['Rise'], axis=0)
            #data_frame_st['Difference'] = (df_st['Difference']/np.timedelta64(1, 'm')).round().astype(int) # Round up as int
            data_frame_st['Difference (mins)'] = 0

            data_frame_st = data_frame_st.drop_duplicates(subset=['Rise'], keep='last', inplace=False)
            columns = ['Rise', 'Set', 'Type', 'Difference (mins)'] # Drop some columns
            df_st_rise_set = pd.DataFrame(data_frame_st, columns=columns)
            small_st_dfs.append(df_st_rise_set)
    
        large_st_df = pd.concat(small_st_dfs, ignore_index=True)

        # Gather all locations passes
        for loc_passes in locations_passes:
            data_frame_loc = pd.DataFrame(loc_passes, columns=['Current', 'Rise', 'Transit', 'Set', 'Type'])

            # Copy without reference
            df_loc = data_frame_loc.copy()
            df_loc['Rise'] = pd.to_datetime(df_loc['Rise'], format="%d/%m/%Y %X")
            df_loc['Set'] = pd.to_datetime(df_loc['Set'], format="%d/%m/%Y %X")
            df_loc['Difference'] = df_loc['Set'].sub(df_loc['Rise'], axis=0)
            data_frame_loc['Difference (mins)'] = (df_loc['Difference']/np.timedelta64(1, 'm')).round().astype(int) # Round up as int

            data_frame_loc = data_frame_loc.drop_duplicates(subset=['Rise'], keep='last', inplace=False)
            df_loc_rise_set = pd.DataFrame(data_frame_loc, columns=columns)    
            small_loc_dfs.append(df_loc_rise_set)    

        # Only for the one to one case
        if(task_amount == 1):
            small__individual_passes_dfs = []
            for loc_df in small_loc_dfs:
                loc_st_passes = pd.concat([small_st_dfs[0], loc_df], ignore_index=True) # Get only 1 gr station
                sorted_loc_st_passes = loc_st_passes.sort_values(by=['Rise']).reset_index(drop=True) # Sort on rise time and reset index
                small__individual_passes_dfs.append(sorted_loc_st_passes) 
            return small__individual_passes_dfs

        # For the rest of the cases (1:5 and 5:5)
        else:    
            large_loc_df = pd.concat(small_loc_dfs, ignore_index=True)   

            # Combine data frames of stations and locations and sort on rise time
            passes = pd.concat([large_st_df, large_loc_df])
            sorted_passes = passes.sort_values(by=['Rise'])

            # Reset index
            final_df = sorted_passes.reset_index(drop=True)

            return [final_df]

    # Delegate to the correct case
    def __process_passes(self, all_passes, st_amount, task_amount):
        tasks_hours = [dt.booking_mins for dt in self._tasks_loc_list]
        
        if(st_amount == 1 and task_amount == 1):
            result = self.__one_to_one_case(all_passes, tasks_hours[:task_amount]) # Get only the hours of the tasks relevant for the case
        elif(st_amount == 1 and task_amount == 5):
            result = self.__one_to_many_case(all_passes)
        else: # Case for 5:5
            result = self.__many_to_many_case(all_passes)

        self.__print_result(result)
        
    def __one_to_one_case(self, passes, hours):
        result = {} # Dictionary with name of the task as key and value will be an array with the finish date with and without bandwidth
        tasks_names = [dt.name for dt in self._tasks_loc_list]
        all_dates = []

        for p in passes:
            dates = []

            # Without Bandwidth
            processed_df = self.__drop_without_bandwidth_1_2_1(p)
            #print(processed_df.to_string())
            date = self.__get_final_deployment_to_ground_date(processed_df, hours[0]) # hours - list of 1 elm
            #print()
            #print(date)
            #print(self.__format_date(date))
            dates.append(self.__format_date(date))
            


            # With Bandwidth
            dates.append('0')

            # By the end
            all_dates.append(dates)

        for i in range(0, len(tasks_names)):
            result[tasks_names[i]] = all_dates[i]
        
        return result


    def __drop_without_bandwidth_1_2_1(self, passes_df):
        # Compare to previous row the value of 'Type'
        match_result = passes_df['Type'].ne(passes_df['Type'].shift()).astype(int)
        passes_df.insert(4, 'Match', match_result)
        passes_df = passes_df[passes_df['Match'] != 0] # Remove those that are duplicates (two rows with the same value in 'Type')
        passes_df = passes_df.drop(columns=['Match']) # Drop the 'Match' column

        # Continuously sum the time spent above a task location
        passes_df['Cumulative time'] = passes_df['Difference (mins)'].cumsum()

        return passes_df.reset_index(drop=True)

    def __get_last_possible_task_for_booking(self, passes_df):
        last_two = passes_df.tail(2)
        last = last_two[last_two['Type'] != 'Home']
        if last.empty:
            return (passes_df[passes_df['Type'] != 'Home']).tail(1)

    def __get_final_deployment_to_ground_date(self, passes, mins):
        # Get the first ground station finish time, after the task hours(in mins) are completed, that completes the booking (sending down the data)
        qualified = passes.query('((`Cumulative time` == ' + str(mins) + ') or (`Cumulative time` > ' + str(mins) + ')) and (Type == "Home")')

        finish_date = qualified.head(1)['Set'].item() # Get the value from series

        return finish_date


    def __print_passes(self, passes):
        data_frame = pd.DataFrame(passes, columns=['Current', 'Rise', 'Transit', 'Set', 'Type'])
        data_frame = data_frame.drop_duplicates(subset=['Rise'], keep='first', inplace=False)
        print(data_frame)

    def __format_date(self, finish_date_str):
        return pd.to_datetime(finish_date_str, format="%d/%m/%Y %X").strftime("%d %b %Y")

    def __print_result(self, dict):
        print()
        print("Bookings can be completed for:")
        print()
        for key, value in dict.items():
            print("    Task " + key + ":")
            print("\tWithout bandwidth: " + value[0])
            print("\tWith bandwidth: " + value[1])


    def print_tasks(self):
        for task in self._tasks_loc_list:
            # Format dates
            start = task.start_date.strftime("%d/%m/%Y %X")
            end = task.end_date.strftime("%d/%m/%Y %X")

            print("Task " + task.name + ":")
            print("\tBooking period: " + self.__format_date(start) + " - " + self.__format_date(end))
            print("\tHour(s) booked: " + str(int(task.booking_mins / 60)))