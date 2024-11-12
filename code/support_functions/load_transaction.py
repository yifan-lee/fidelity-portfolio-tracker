import pandas as pd
import os
import glob

def load_transaction(data_folder_path, transaction_file_pattern):
    transaction_file_path_pattern = os.path.join(data_folder_path, transaction_file_pattern)
    transaction_files = glob.glob(transaction_file_path_pattern)

    transaction_list = [pd.read_csv(file, usecols=range(13)) for file in transaction_files]
    transaction_list = [transaction[transaction['Account'].notna()] for transaction in transaction_list]

    transactions = pd.concat(transaction_list, ignore_index=True)
    
    transactions['Run Date'] = pd.to_datetime(transactions['Run Date'], format=' %m/%d/%Y')
    transactions['Settlement Date'] = pd.to_datetime(transactions['Settlement Date'], format='%m/%d/%Y')
    transactions['Symbol'] = transactions['Symbol'].str.replace(' ', '', regex=True)
    transactions['Symbol'] = transactions['Symbol'].replace('', 'Transfer')
    
    return transactions