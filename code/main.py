from support_functions import Portfolio, data_loader

data_folder_path = "./data"
transaction_file_pattern = "Accounts_History_*.csv"
position_file_pattern = "Portfolio_Positions_*.csv"
account_number_dict = {
    "individual": "Z23390746",
    "pension": "86964",
    "HSA": "241802439",
    "Z06872898": "Z06872898"
}

transactions = data_loader.load_transaction(data_folder_path, transaction_file_pattern)
position = data_loader.load_position(data_folder_path, position_file_pattern)

current_portfolio = Portfolio(transactions=transactions, position=position, account_number_dict=account_number_dict)
account_symbol = 'individual'
current_portfolio.set_current_account(account_symbol)
current_portfolio.show_investment_distribution(account_symbol)
current_portfolio.show_account_irr(account_symbol)

# print(current_portfolio.pension_transactions)