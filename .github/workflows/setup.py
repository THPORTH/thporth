import subprocess
import sys


packages_to_install = ['selenium', 'gspread', 'bs4', 'oauth2client']
try:
    for package_to_install in packages_to_install:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_to_install])

    input('[+] All modules successfully installed!\nPress Enter to end...')

except Exception as err:
    input(f'[-] Error installing modules: {err}\nPress Enter to end...')


# https://fiverr.com/ahmed_elsisi #
