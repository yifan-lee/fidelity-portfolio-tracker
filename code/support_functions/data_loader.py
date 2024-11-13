import pandas as pd
import os
import glob

def load_position(data_folder_path, position_file_pattern):
    position_file_path_pattern = os.path.join(data_folder_path, position_file_pattern)
    position_file = glob.glob(position_file_path_pattern)

    if len(position_file)==1:
        position = pd.read_csv(position_file[0])
        position = position[position['Type'].notna()]
        position['Current Value'] = transfer_dollar_to_float(position['Current Value'])
        position['Cost Basis Total'] = transfer_dollar_to_float(position['Cost Basis Total'])
    elif len(position_file)==0:
        print("No file starting with 'Portfolio_Positions' found in the specified folder.")
        return 0
    else:
        print("More than one file starting with 'Portfolio_Positions' found in the specified folder.")
        return 0
    
    return position

def load_transaction(data_folder_path, transaction_file_pattern):
    transaction_file_path_pattern = os.path.join(data_folder_path, transaction_file_pattern)
    transaction_files = glob.glob(transaction_file_path_pattern)

    transaction_list = [pd.read_csv(file, usecols=range(13)) for file in transaction_files]
    transaction_list = [transaction[transaction['Account'].notna()] for transaction in transaction_list]

    transactions = pd.concat(transaction_list, ignore_index=True)
    
    transactions['Run Date'] = pd.to_datetime(transactions['Run Date'], format=' %m/%d/%Y').dt.date
    transactions['Settlement Date'] = pd.to_datetime(transactions['Settlement Date'], format='%m/%d/%Y').dt.date
    transactions['Symbol'] = transactions['Symbol'].str.replace(' ', '', regex=True)
    transactions['Symbol'] = transactions['Symbol'].replace('', 'Transfer')
    transactions = transactions.sort_values(by='Run Date').reset_index(drop=True)
    
    return transactions

def transfer_dollar_to_float(dat):
    return dat.str.replace('$', '', regex=False).astype(float)


