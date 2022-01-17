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
        self._sats_list = FileHandler().load_sat('./data/sats.txt') # For more orbits use './data/orbits.txt'

        # Read Ground Stations coordinates
        self._stations_list = FileHandler().load_st('./data/grStations.txt') # './data/stations.txt' - is a smaller file

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
            
            if(len(passes_station) == 0):
                print('Satellite does not pass above the station with index: ' + i)

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
        time_step = 3600 # 1h
        loc_type = 'Home' if is_station else 'Task'
        passes = []
        current_time = start

        # Calculate the passes
        while current_time < end:
            loc.date = current_time
            sat.compute(loc)
            rt = ephem.localtime(sat.rise_time).strftime("%d/%m/%Y %X")
            tt = ephem.localtime(sat.transit_time).strftime("%d/%m/%Y %X")
            st = ephem.localtime(sat.set_time).strftime("%d/%m/%Y %X")
            passes.append((current_time.strftime("%d/%m/%Y %X"), rt, tt, st, loc_type))
            #current_time += datetime.timedelta(seconds=time_step) OLD WAY OF INCREMENTING  

            end_time = sat.set_time.datetime() # Convert to datetime
            current_time = end_time + datetime.timedelta(seconds=time_step)
        return passes

    # Combine data frames
    def __gather_passes(self, stations_passes, locations_passes, task_amount):
        small_st_dfs = []
        small_loc_dfs = []
        task_index = 0
        tasks_names = [dt.name for dt in self._tasks_loc_list]

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
            data_frame_st['Name'] = ''

            data_frame_st = data_frame_st.drop_duplicates(subset=['Rise'], keep='last', inplace=False)
            columns = ['Rise', 'Set', 'Type', 'Difference (mins)', 'Name'] # Drop some columns
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
            data_frame_loc['Name'] = tasks_names[task_index]
            task_index += 1

            data_frame_loc = data_frame_loc.drop_duplicates(subset=['Rise'], keep='last', inplace=False)
            df_loc_rise_set = pd.DataFrame(data_frame_loc, columns=columns)    
            small_loc_dfs.append(df_loc_rise_set)    

        # Only for the one to one case
        if(task_amount == 1):
            small__individual_passes_dfs = []
            for loc_df in small_loc_dfs:
                loc_st_passes = pd.concat([small_st_dfs[0], loc_df], ignore_index=True) # Get only 1 gr station
                sorted_loc_st_passes = loc_st_passes.sort_values(by=['Rise'], ascending=True).reset_index(drop=True) # Sort on rise time and reset index
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
        else: # Case for 1:5 and 5:5
            result = self.__x_to_many_case(all_passes[0], tasks_hours[:task_amount]) # Passes is a list with 1 item

        self.__print_result(result)
        
    def __one_to_one_case(self, passes, hours):
        result = {} # Dictionary with name of the task as key and value will be an array with the finish date with and without bandwidth
        tasks_names = [dt.name for dt in self._tasks_loc_list]
        all_dates = []

        for p in passes:
            dates = []

            # Without Bandwidth
            processed_df = self.__without_bandwidth_1_to_1(p)
            date = self.__get_final_deployment_to_ground_date(processed_df, hours)[0] # hours - list of 1 elm; list of 1 elm is returned
            dates.append(self.__format_date(date))

            # With Bandwidth
            processed_df_wb = self.__with_bandwidth_1_to_1(p)
            date_wb = self.__get_final_deployment_to_ground_date(processed_df_wb, hours)[0] # hours - list of 1 elm; list of 1 elm is returned
            dates.append(self.__format_date(date_wb))

            # By the end append each date list to a new collection
            all_dates.append(dates)

        for i in range(0, len(tasks_names)):
            result[tasks_names[i]] = all_dates[i]
        
        return result

    def __x_to_many_case(self, passes, hours):
        result = {} # Dictionary with name of the task as key and value will be an array with the finish date with and without bandwidth
        tasks_names = [dt.name for dt in self._tasks_loc_list]

        # Without Bandwidth
        processed_df = self.__without_bandwidth_1_to_5(passes)
        dates = self.__get_final_deployment_to_ground_date(processed_df, hours)

        for i in range(0, len(tasks_names)):
            result[tasks_names[i]] = [dates[i]]

        # With Bandwidth
        processed_df = self.__with_bandwidth_1_to_5(passes)
        dates_wb = self.__get_final_deployment_to_ground_date(processed_df, hours)

        for i in range(0, len(tasks_names)):
            result[tasks_names[i]].append(dates_wb[i])

        return result

    def __without_bandwidth_1_to_1(self, passes_df):
        # Copy without reference
        passes = passes_df.copy()

        # Compare to previous row the value of 'Type'
        match_result = passes['Type'].ne(passes['Type'].shift()).astype(int)
        passes.insert(4, 'Match', match_result)
        passes = passes[passes['Match'] != 0] # Remove those that are duplicates (two rows with the same value in 'Type')
        passes = passes.drop(columns=['Match']) # Drop the 'Match' column

        # Continuously sum the time spent above a task location
        passes['Cumulative time'] = passes['Difference (mins)'].cumsum()

        return passes.reset_index(drop=True)

    # Function for manipulating the df, so it is Task, Home, Task, Home ...
    def __with_bandwidth_1_to_1(self, passes_df):
        count_task = 0
        count_home = 0
        
        # Copy without reference
        passes = passes_df.copy()

        for index, row in passes.iterrows():
            #is_home = True if row['Type'] == 'Home' else False
            
            loc_type = row['Type']
            if(count_task == 0 and loc_type == 'Task'):
                count_task += 1
                continue
            elif(count_task == 0 and loc_type == 'Home'):
                passes.drop(index, inplace=True)
                continue
            elif(count_task == 1 and loc_type == 'Task'):
                passes.drop(index, inplace=True)
                continue
            elif(count_task == 1 and loc_type == 'Home'):
                if(count_home < 2):
                    count_home += 1
                elif(count_home == 2):
                    count_task = 0 # Reset task count
                    count_home = 0 # Reset home count (it reached 3 homes)

        # Continuously sum the time spent above a task location
        passes['Cumulative time'] = passes['Difference (mins)'].cumsum()

        return passes.reset_index(drop=True)

    def __without_bandwidth_1_to_5(self, passes_df):
        task_taken = 0
        tasks_names = [dt.name for dt in self._tasks_loc_list]
        
        # Copy without reference
        passes = passes_df.copy()

        for index, row in passes.iterrows():
            loc_type = row['Type']
            if(task_taken == 0 and loc_type == 'Task'):
                task_taken += 1
                continue
            elif(task_taken == 0 and loc_type == 'Home'):
                passes.drop(index, inplace=True)
                continue
            elif(task_taken == 1 and loc_type == 'Task'):
                passes.drop(index, inplace=True)
                continue
            elif(task_taken == 1 and loc_type == 'Home'):
                task_taken = 0

        passes['Cumulative time'] = 0

        for name in tasks_names:
            qualified = passes.query('Name == "' + name + '"')
            qualified['Cumulative time'] = qualified['Difference (mins)'].cumsum().astype(int)
            #print(qualified.to_string()) TODO: Check with the end dates
            #print()
            passes.update(qualified) # Update initial df

        # Convert values from float to int
        passes['Cumulative time'] = passes['Cumulative time'].apply(np.int32)
        passes['Difference (mins)'] = passes['Difference (mins)'].apply(np.int32)

        return passes.reset_index(drop=True)
    
    def __with_bandwidth_1_to_5(self, passes_df):
        tasks_names = [dt.name for dt in self._tasks_loc_list]
        processed_df_wb = self.__with_bandwidth_1_to_1(passes_df) # Can reuse this fuc because we need Task, Home, Task, Home anyway 
        processed_df_wb['Cumulative time'] = 0

        for name in tasks_names:
            qualified = processed_df_wb.query('Name == "' + name + '"')
            qualified['Cumulative time'] = qualified['Difference (mins)'].cumsum().astype(int)
            #print(qualified.to_string()) TODO: Check with the end dates
            #print()
            processed_df_wb.update(qualified) # Update initial df

        # Convert values from float to int
        processed_df_wb['Cumulative time'] = processed_df_wb['Cumulative time'].apply(np.int32)
        processed_df_wb['Difference (mins)'] = processed_df_wb['Difference (mins)'].apply(np.int32)

        return processed_df_wb.reset_index(drop=True)

    def __get_last_possible_task_for_booking(self, passes_df):
        last_two = passes_df.tail(2)
        last = last_two[last_two['Type'] != 'Home']
        if last.empty:
            return (passes_df[passes_df['Type'] != 'Home']).tail(1)

    def __get_final_deployment_to_ground_date(self, passes, list_mins):
        finish_dates = []
        tasks_names = [dt.name for dt in self._tasks_loc_list]

        if(len(list_mins) > 1):
            for i in range(0, len(list_mins)):
                mins = list_mins[i]
                qualified = passes.query('Name == "' + tasks_names[i] + '"')
                qualified = qualified.query('(`Cumulative time` == ' + str(mins) + ') or (`Cumulative time` > ' + str(mins) + ')')
                
                if(len(qualified.index) == 0):
                    print('Satellite does not pass above this location: ' + tasks_names[i])

                idx = qualified.head(1).index.item()

                for index, row in qualified.iterrows():
                    if(index != idx):
                        passes.drop(index, inplace=True)

        for i in range(0, len(list_mins)):
            mins = list_mins[i]
            if(len(list_mins) == 1):
                # Get the first ground station finish time, after the task hours(in mins) are completed, that completes the booking (sending down the data)
                qualified = passes.query('((`Cumulative time` == ' + str(mins) + ') or (`Cumulative time` > ' + str(mins) + ')) and (Type == "Home")')

                if(len(qualified.index) == 0):
                    print('Satellite does not pass above this location: ' + tasks_names[i])

                finish_date = qualified.head(1)['Set'].item() # Get the value from series
                return [finish_date]
            else:
                qualified = passes.query('Name == "' + tasks_names[i] + '"')
                
                # Make sure the df is not empty
                if(len(qualified.index) > 0):
                    idx = qualified.tail(1).index.item()
                    finish_date = passes.loc[idx + 1]['Set'] # Select Home
                    finish_dates.append(self.__format_date(finish_date))
                else:
                    finish_dates.append('0')

        return finish_dates


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