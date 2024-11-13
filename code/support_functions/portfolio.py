from datetime import datetime
import pandas as pd
import numpy as np
from scipy.optimize import root_scalar


class Portfolio:
    def __init__(self, transactions, position):
        self.transactions = transactions
        self.position = position

        self.today = datetime.now().date()
        self.individual_transactions = self.transactions[
            self.transactions["Account"] == "Individual Z23390746"
        ]
        self.individual_position = self.position[
            self.position["Account Number"] == "Z23390746"
        ]

    def show_investment_distribution(self):
        investment_distribution = self.get_investment_distribution()
        investment_distribution['Percent'] = [f"{x * 100:.2f}%" for x in investment_distribution['Percent']]
        print(pd.DataFrame(investment_distribution))

    def get_investment_distribution(self):
        total_investment = self.get_total_investment()
        stock_investment = self.get_stock_investment()
        bill_investment = self.get_bill_investment()
        other_investment = self.get_other_investment()
        result = {
                "Class": ["stock", "bill", "other", "total"],
                "Amount": [
                    stock_investment,
                    bill_investment,
                    other_investment,
                    total_investment,
                ],
                "Percent": [
                    stock_investment / total_investment,
                    bill_investment / total_investment,
                    other_investment / total_investment,
                    total_investment / total_investment,
                ],
            }

        return result

    def get_total_investment(self):
        total_investment = self.individual_transactions[
            self.individual_transactions["Symbol"] == "Transfer"
        ]["Amount ($)"].sum()
        return total_investment

    def get_stock_investment(self):
        stock_position = self.individual_position[
            ~(self.individual_position["Description"] == "HELD IN MONEY MARKET")
            & ~(self.individual_position["Description"].str.contains("BILLS"))
        ]
        return stock_position["Cost Basis Total"].sum()

    def get_bill_investment(self):
        bill_position = self.individual_position[
            (self.individual_position["Description"].str.contains("BILLS"))
        ]
        return bill_position["Cost Basis Total"].sum()

    def get_other_investment(self):
        return (
            self.get_total_investment()
            - self.get_stock_investment()
            - self.get_bill_investment()
        )
        
        
    def show_stock_irr(self):
        stock_irr = self.get_stock_irr()
        stock_irr_nice_look = pd.DataFrame({
            'Stock': stock_irr.keys(),
            'irr': [f"{(stock_irr[x]) * 100:.2f}%" for x in stock_irr.keys()]
        })
        print(pd.DataFrame(stock_irr_nice_look))
        
    def get_stock_irr(self):
        self.add_total_current_value_to_individual_position()
        self.set_merged_individual_position_transaction()
        self.add_time_diff_in_merged_individual_position_transaction()
        
        unique_symbols = self.merged_individual_position_transaction['Symbol'].unique()
        stock_list = [element for element in unique_symbols if 'FZFXX' not in element and not element[0].isdigit()]
        
        result_dict = {x: self.calculate_irr(x) for x in stock_list}
        
        return result_dict
        
        
    def filter_merged_transactions_by_symbol(self, symbol):
        return self.merged_individual_position_transaction[self.merged_individual_position_transaction['Symbol']==symbol]

    def add_total_current_value_to_individual_position(self):
        if 'Transfer' in self.individual_position['Symbol'].values:
            print("Total current value has been added")
            return 
        
        total_current_value = self.get_total_current_value()
        new_rows = pd.DataFrame({
            "Symbol": ['Transfer'],
            "Current Value": -total_current_value
        })
        self.individual_position = pd.concat([self.individual_position, new_rows], ignore_index=True)

    def set_merged_individual_position_transaction(self):
        new_rows = pd.DataFrame({
            "Run Date": [self.today] * len(self.individual_position),
            "Symbol": self.individual_position["Symbol"],
            "Amount ($)": self.individual_position["Current Value"]
        })

        self.merged_individual_position_transaction = pd.concat([self.individual_transactions, new_rows], ignore_index=True)
        
    def add_time_diff_in_merged_individual_position_transaction(self):
        self.merged_individual_position_transaction.loc[:, "time_diffs_in_year"] = (
            self.today - self.merged_individual_position_transaction.loc[:, "Run Date"]
        ).apply(lambda x: x.days) / 365.25

    def get_total_current_value(self):
        return self.individual_position["Current Value"].sum()

    def calculate_irr(self, symbol, lower_bound=-0.999, upper_bound=5):
        transactions = self.filter_merged_transactions_by_symbol(symbol)

        def npv(rate):
            return np.sum(
                transactions["Amount ($)"]
                * (1 + rate) ** transactions["time_diffs_in_year"]
            )

        result = root_scalar(npv, bracket=[lower_bound, upper_bound], method="bisect")

        if result.converged:
            return result.root
        else:
            raise ValueError(
                "No solution found for the rate that satisfies the equation."
            )




    # def get_overall_irr(self):
    #     total_current_value = self.get_total_current_value()

    #     Transfer_transaction = self.individual_transactions[
    #         self.individual_transactions["Symbol"] == "Transfer"
    #     ]
    #     new_rows = pd.DataFrame(
    #         {
    #             "Run Date": self.today,
    #             "Symbol": ["Transfer"],
    #             "Amount ($)": -total_current_value,
    #         }
    #     )
    #     Transfer_transaction = pd.concat(
    #         [Transfer_transaction, new_rows], ignore_index=True
    #     )
    #     overall_irr = self.calculate_irr(Transfer_transaction)

    #     return f"{(overall_irr) * 100:.2f}%"


