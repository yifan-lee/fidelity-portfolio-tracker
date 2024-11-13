import pandas as pd
import numpy as np
import os
import importlib
from datetime import datetime

# base_path = '/Users/yifanli/Github/fidelity-portfolio-tracker'
# os.chdir(base_path)

from support_functions import Portfolio, data_loader


data_folder_path = './data'
transaction_file_pattern = 'Accounts_History_*.csv'
position_file_pattern = 'Portfolio_Positions_*.csv'

transactions = data_loader.load_transaction(data_folder_path, transaction_file_pattern)
position = data_loader.load_position(data_folder_path, position_file_pattern)

current_portfolio = Portfolio(transactions=transactions, position=position)

print(current_portfolio.get_investment_distribution())