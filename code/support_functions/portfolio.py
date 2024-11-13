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

    def get_investment_distribution(self):
        total_investment = self.get_total_investment()
        stock_investment = self.get_stock_investment()
        bill_investment = self.get_bill_investment()
        other_investment = self.get_other_investment()
        result = pd.DataFrame(
            {
                "Class": ["stock", "bill", "other", "total"],
                "Amount": [
                    stock_investment,
                    bill_investment,
                    other_investment,
                    total_investment,
                ],
                "Percent": [
                    f"{(stock_investment / total_investment) * 100:.2f}%",
                    f"{(bill_investment / total_investment) * 100:.2f}%",
                    f"{(other_investment / total_investment) * 100:.2f}%",
                    f"{(total_investment / total_investment) * 100:.2f}%",
                ],
            }
        )

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

    def get_overall_irr(self):
        total_current_value = self.get_total_current_value()

        Transfer_transaction = self.individual_transactions[
            self.individual_transactions["Symbol"] == "Transfer"
        ]
        new_rows = pd.DataFrame(
            {
                "Run Date": self.today,
                "Symbol": ["Transfer"],
                "Amount ($)": -total_current_value,
            }
        )
        Transfer_transaction = pd.concat(
            [Transfer_transaction, new_rows], ignore_index=True
        )
        overall_irr = self.calculate_irr(Transfer_transaction)

        return f"{(overall_irr) * 100:.2f}%"

    def get_total_current_value(self):
        return self.individual_position["Current Value"].sum()

    def calculate_irr(self, transactions, lower_bound=-0.999, upper_bound=5):
        transactions_copy = transactions.copy()
        transactions_copy["time_diffs_in_year"] = (
            self.today - transactions_copy["Run Date"]
        ).apply(lambda x: x.days) / 365.25

        def npv(rate):
            return np.sum(
                transactions_copy["Amount ($)"]
                * (1 + rate) ** transactions_copy["time_diffs_in_year"]
            )

        result = root_scalar(npv, bracket=[lower_bound, upper_bound], method="bisect")

        if result.converged:
            return result.root
        else:
            raise ValueError(
                "No solution found for the rate that satisfies the equation."
            )
