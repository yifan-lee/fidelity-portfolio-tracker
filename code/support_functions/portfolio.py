from datetime import datetime
import pandas as pd
import numpy as np
from scipy.optimize import root_scalar


class Portfolio:
    """
    A class to represent a fidelity portfolio.

    Attributes
    ----------
    transactions: pd.DataFrame
        All historial transactions.
    position: pd.DataFrame
        Current balance in the account.
    today: datetime.date
        Today's date
    individual_transactions: pd.DataFrame
        Transactions under account "Individual Z23390746"
    individual_position: pd.DataFrame
        Position under account "Individual Z23390746"

    Methods
    -------
    show_investment_distribution:
        display the result of get_investment_distribution.
    get_investment_distribution:
        get the distribution of investment amony differnet asset.
    get_total_investment:
        get total investment amount in dollar.
    get_stock_investment:
        get amount of stock investment in dollar.
    get_bill_investment:
        get amount of bill investment in dollar.
    get_other_investment:
        get amount of other investment in dollar.
    show_stock_irr:
        display the result of get_stock_irr.
    get_stock_irr:
        get the irr of each stock.
    add_total_current_value_to_individual_position:
        ---
    get_total_current_value:
        ---
    set_merged_individual_position_transaction:
        merge individual_position and individual_transaction.
    add_time_diff:
        ---
    calculate_irr(symbol_list, lower_bound=-0.999, upper_bound=5):
        filter all transactions with symbol in symbol_list. Then calculate the irr of these transactions.
    filter_merged_transactions_by_symbol(symbol_list):
        filter all transactions with symbol in symbol_list.
    """

    def __init__(self, transactions, position):
        self.transactions = transactions
        self.position = position

        self.today = datetime.now().date()
        self.individual_transactions = self.transactions[
            self.transactions["Account"] == "Individual Z23390746"
        ]
        self.pension_transactions = self.transactions[
            self.transactions["Account"] == "ERNST & YOUNG 401(K) 86964"
        ]
        self.HSA_transactions = self.transactions[
            self.transactions["Account"] == "Health Savings Account 241802439"
        ]
        self.cash_transactions = self.transactions[
            self.transactions["Account"] == "Cash Management (Individual) Z06872898"
        ]
        
        self.individual_position = self.position[
            self.position["Account Number"] == "Z23390746"
        ]
        self.pension_position = self.position[
            self.position["Account Number"] == "86964"
        ]
        self.HSA_position = self.position[
            self.position["Account Number"] == "241802439"
        ]
        self.cash_position = self.position[
            self.position["Account Number"] == "Z06872898"
        ]
        

    def show_investment_distribution(self):
        investment_distribution = self.get_investment_distribution()
        investment_distribution["Percent"] = [
            f"{x * 100:.2f}%" for x in investment_distribution["Percent"]
        ]
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
            & ~(self.individual_position["Description"].str.contains("BILLS", na=False))
        ]
        return stock_position["Cost Basis Total"].sum()

    def get_bill_investment(self):
        bill_position = self.individual_position[
            (self.individual_position["Description"].str.contains("BILLS", na=False))
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
        stock_irr_nice_look = pd.DataFrame(
            {
                "Stock": stock_irr.keys(),
                "irr": [f"{(stock_irr[x]) * 100:.2f}%" for x in stock_irr.keys()],
            }
        )
        print(pd.DataFrame(stock_irr_nice_look))

    def get_stock_irr(self):
        self.add_total_current_value_to_individual_position()
        self.set_merged_individual_position_transaction()
        self.merged_individual_position_transaction = self.add_time_diff(self.merged_individual_position_transaction)

        unique_symbols = self.merged_individual_position_transaction["Symbol"].unique()
        stock_list = [
            element
            for element in unique_symbols
            if "FZFXX" not in element
            and not element[0].isdigit()
            and "Pending" not in element
        ]
        result_dict = {x: self.calculate_irr(self.filter_merged_transactions_by_symbol([x])) for x in stock_list}
        if "Transfer" in stock_list:
            stock_list.remove("Transfer")
        transactions = self.filter_merged_transactions_by_symbol(stock_list)
        result_dict["stock"] = self.calculate_irr(transactions)

        return result_dict

    def add_total_current_value_to_individual_position(self):
        if "Transfer" in self.individual_position["Symbol"].values:
            print("Total current value has been added")
            return

        total_current_value = self.get_total_current_value()
        new_rows = pd.DataFrame(
            {"Symbol": ["Transfer"], "Current Value": -total_current_value}
        )
        self.individual_position = pd.concat(
            [self.individual_position, new_rows], ignore_index=True
        )

    def get_total_current_value(self):
        return self.individual_position["Current Value"].sum()

    def set_merged_individual_position_transaction(self):
        new_rows = pd.DataFrame(
            {
                "Run Date": [self.today] * len(self.individual_position),
                "Symbol": self.individual_position["Symbol"],
                "Amount ($)": self.individual_position["Current Value"],
            }
        )

        self.merged_individual_position_transaction = pd.concat(
            [self.individual_transactions, new_rows], ignore_index=True
        )

    def add_time_diff(self, transactions):
        transactions_copy = transactions.copy()
        if not 'time_diffs_in_year' in transactions_copy.columns:
            transactions_copy.loc[:, "time_diffs_in_year"] = (
                self.today - transactions_copy.loc[:, "Run Date"]
            ).apply(lambda x: x.days) / 365.25
        else:
            print("Column time_diffs_in_year exists")
        return transactions_copy
        

    def calculate_irr(self, transactions, lower_bound=-0.999, upper_bound=5):

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

    def filter_merged_transactions_by_symbol(self, symbol_list):
        return self.merged_individual_position_transaction[
            self.merged_individual_position_transaction["Symbol"].isin(symbol_list)
        ]
        
    
