from menu import Menu
from transitCalculator import TransitCalculator

def main():
    tc_instance = TransitCalculator()
    tc_instance.prepare()

    while(True):
        Menu().print_menu()
        option = ''
        try:
            print()
            option = int(input('Enter your choice: '))
        except:
            Menu().clear()
            print('Wrong input. Please enter a number ...')
        #Check what choice was entered and act accordingly
        if option == 1:
            __option1(tc_instance)
        elif option == 2:
            __option2(tc_instance)
        elif option == 3:
            __option3(tc_instance)
        elif option == 4:
            print('Goodbye!')
            print()
            exit()
        else:
            print('Invalid option. Please enter a number between 1 and 4.')


def __option1(tc_instance):
    Menu().clear()
    print('Handling option \'Option 1\'...')
    print()
    tc_instance.calculate(1, 1)
    print()
    print()

def __option2(tc_instance):
    Menu().clear()
    print('Handling option \'Option 2\'...')
    print('Not implemented yet!!!')
    print()
    #tc_instance.calculate(1, 5)
    print()
    print()

def __option3(tc_instance):
    Menu().clear()
    print('Handling option \'Option 3\'...')
    print('Not implemented yet!!!')
    print()
    #tc_instance.calculate(5, 5)
    print()
    print()

if __name__ == "__main__":
    main()