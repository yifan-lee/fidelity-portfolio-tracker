import pandas as pd
import os
import glob

def load_position(data_folder_path, position_file_pattern):
    position_file_path_pattern = os.path.join(data_folder_path, position_file_pattern)
    position_file = glob.glob(position_file_path_pattern)

    if len(position_file)==1:
        position = pd.read_csv(position_file[0])
        position = position[position['Type'].notna()]
        position['Current Value'] = position['Current Value'].str.replace('$', '', regex=False).astype(float)
    elif len(position_file)==0:
        print("No file starting with 'Portfolio_Positions' found in the specified folder.")
        return 0
    else:
        print("More than one file starting with 'Portfolio_Positions' found in the specified folder.")
        return 0
    
    return position
