from datetime import datetime
import pandas as pd

class Portfolio:
    def __init__(self, transactions, position):
        self.transactions = transactions
        self.position = position
        
        self.today = datetime.now().date()
        self.individual_transactions = self.transactions[self.transactions['Account']=='Individual Z23390746']
        self.individual_position = self.position[self.position['Account Number']=='Z23390746']
        
    def get_investment_distribution(self):
        total_investment = self.get_total_investment()
        stock_investment = self.get_stock_investment()
        bill_investment = self.get_bill_investment()
        other_investment = self.get_other_investment()
        result = pd.DataFrame({
            'Class': ['stock','bill','other','total'],
            'Amount': [stock_investment, bill_investment, other_investment, total_investment],
            'Percent': [f"{(stock_investment / total_investment) * 100:.2f}%",
                        f"{(bill_investment / total_investment) * 100:.2f}%",
                        f"{(other_investment / total_investment) * 100:.2f}%",
                        f"{(total_investment / total_investment) * 100:.2f}%"]
        })
        
        return result
    
    def get_total_investment(self):
        total_investment = self.individual_transactions[self.individual_transactions['Symbol']=='Transfer']['Amount ($)'].sum()
        return total_investment
    
    def get_stock_investment(self):
        stock_position = self.individual_position[~(self.individual_position['Description']=='HELD IN MONEY MARKET') & ~(self.individual_position['Description'].str.contains('BILLS'))]
        return stock_position['Cost Basis Total'].sum()
    
    def get_bill_investment(self):
        bill_position = self.individual_position[(self.individual_position['Description'].str.contains('BILLS'))]
        return bill_position['Cost Basis Total'].sum()
    
    def get_other_investment(self):
        return self.get_total_investment()-self.get_stock_investment()-self.get_bill_investment()
        
    
        
