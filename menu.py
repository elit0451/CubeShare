import os

class Menu:
    _menu_options_ = {
        1: '1 SAT; 1 ST; 1 T  (Current)',
        2: '1 SAT; 1 ST; 5 T',
        3: '1 SAT; 5 ST; 5 T',
        4: 'Exit',
    }

    def print_menu(self):
        print()
        print("************ Welcome to CubeShare Simulation **************")
        print()
        for key in self._menu_options_.keys():
            print (key, '--', self._menu_options_[key] )

        print()
        print('Dictionary:')
        print('\tSAT = Satellite')
        print('\tST = Ground Station')
        print('\tT = Task')

    def clear(self):
        os.system('cls' if os.name=='nt' else 'clear')

    def display_result():
        print('WIP')