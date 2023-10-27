import os 
import datetime

BASE_URL = "https://learn.microsoft.com/en-us/azure"
ROOT_FOLDER = '../well-architected' 
TODAY = datetime.date.today().strftime('%Y-%m')
BUILD_DIR = os.path.join(ROOT_FOLDER, f'../build/{TODAY}')