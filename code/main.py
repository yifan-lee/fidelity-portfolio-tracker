import pandas as pd
import os
import glob
import importlib

base_path = '/Users/yifanli/Github/fidelity-portfolio-tracker'
os.chdir(base_path)

from support_functions import portfolio, load_transaction, load_position

# importlib.reload(load_transaction)
# load_transaction = load_transaction.load_transaction
# importlib.reload(load_position)
# load_position = load_position.load_position

data_folder_path = './data'
transaction_file_pattern = 'Accounts_History_*.csv'
position_file_pattern = 'Portfolio_Positions_(*).csv'

transactions = load_transaction(data_folder_path, transaction_file_pattern)
position, current_date = load_position(data_folder_path, position_file_pattern)