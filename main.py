from support_functions.display_percentage import display_percentage
from support_functions.data_loader import load_position, load_transaction
from support_functions.portfolio import Portfolio,IndividualPortfolio,PensionPortfolio,HSAPortfolio

data_folder_path = "./data"
transaction_file_pattern = "Accounts_History_*.csv"
position_file_pattern = "Portfolio_Positions_*.csv"

transactions = load_transaction(data_folder_path, transaction_file_pattern)
position = load_position(data_folder_path, position_file_pattern)
portfolio = Portfolio(transactions=transactions, position=position)
individualPortfolio = IndividualPortfolio(transactions, position)
pensionPortfolio = PensionPortfolio(transactions, position)
hsaPortfolio = HSAPortfolio(transactions, position)


result = individualPortfolio.get_account_summary()
print('Display individual account summary')
display_percentage(result,['Percentage','IRR'])

result = individualPortfolio.get_all_stock_summary()
print('Display individual account stock summary')
display_percentage(result,['Percentage','IRR'])

result = individualPortfolio.get_all_bond_summary(showExpiredBond=True)
print('Display individual account bond summary')
display_percentage(result,['Percentage','IRR'])


result = pensionPortfolio.get_all_stock_summary(colName='Description')
print('Display 401k account summary')
display_percentage(result,['Percentage','IRR'])

result = hsaPortfolio.get_all_stock_summary(colName='Description')
print('Display HSA account summary')
display_percentage(result,['Percentage','IRR'])