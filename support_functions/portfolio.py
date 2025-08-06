from datetime import datetime,date
import pandas as pd
import numpy as np
from support_functions.compute_irr import compute_irr


class Portfolio:
    def __init__(self, transactions, position):
        self.transactions = transactions
        self.position = position
        self.cob = date.today()
        
        account_number_dic = {
            "Individual":'Z23390746',
            "401k":'86964',
            "HSA":'241802439',
            "Cash":'Z06872898'
        }
        
        self.individualTransactions = transactions[transactions['Account Number']==account_number_dic["Individual"]]
        self.individualPosition = position[position['Account Number']==account_number_dic["Individual"]]
        self.pensionTransactions = transactions[transactions['Account Number']==account_number_dic["401k"]]
        self.pensionPosition = position[position['Account Number']==account_number_dic["401k"]]
        self.HSATransactions = transactions[transactions['Account Number']==account_number_dic["HSA"]]
        self.HSAPosition = position[position['Account Number']==account_number_dic["HSA"]]
        self.cashTransactions = transactions[transactions['Account Number']==account_number_dic["Cash"]]
        self.cashPosition = position[position['Account Number']==account_number_dic["Cash"]]
        
        
        self.cashSymbols = ['FZFXX**','FZFXX']
        self.otherSymbols = ['Pending Activity','','Transfer']
        self.bondSymbols = self.get_bond_symbol_list()
        self.stockSymbols = self.get_stock_symbol_list()
        
    def get_individual_account_summary(self):
        bondSymbols = self.get_bond_symbol_list()
        bondTotalValue = self.get_total_symbols_value(bondSymbols)
        bondTotalIrr = self.get_combined_symbol_irr(bondSymbols)
        
        stockSymbols = self.get_stock_symbol_list()
        stockTotalValue = self.get_total_symbols_value(stockSymbols)
        stockTotalIrr = self.get_combined_symbol_irr(stockSymbols)
        
        cashSymbols = self.cashSymbols
        cashTotalValue = self.get_total_symbols_value(cashSymbols)
        cashTotalIrr = self.get_combined_symbol_irr(cashSymbols)
        
        totalValue = self.individualPosition['Current Value'].sum()
        result = pd.DataFrame({
            'Type':['bond','stock','cash'],
            'Value': [bondTotalValue,stockTotalValue,cashTotalValue],
            'Percentage':[bondTotalValue,stockTotalValue,cashTotalValue]/totalValue,
            'IRR':[bondTotalIrr, stockTotalIrr, cashTotalIrr]
        } 
        )
        return result
    
        
    def get_all_stock_summary(self):
        stockSymbols = self.get_stock_symbol_list()
        currentValueResult = self.get_symbol_current_values(stockSymbols)
        irrResult = self.get_symbol_irrs(stockSymbols)
        holdingPeriodResult = self.get_symbol_holding_period(stockSymbols)
        result = pd.merge(currentValueResult, irrResult, on='Symbol')
        result = pd.merge(result, holdingPeriodResult, on='Symbol')
        result = result.sort_values(by='Current Value', ascending=False)
        return result
    
    def get_all_bond_summary(self):
        bondSymbols = self.get_bond_symbol_list()
        currentValueResult = self.get_symbol_current_values(bondSymbols)
        irrResult = self.get_symbol_irrs(bondSymbols)
        holdingPeriodResult = self.get_symbol_holding_period(bondSymbols)
        result = pd.merge(currentValueResult, irrResult, on='Symbol')
        result = pd.merge(result, holdingPeriodResult, on='Symbol')
        result = result.sort_values(by='Current Value', ascending=False)
        return result
    
    def get_all_bond_irr(self):
        bondSymbols = self.get_bond_symbol_list()
        result = self.get_symbol_irrs(bondSymbols)
        return result
    
    
    def get_symbol_holding_period(self, listSymbols: list, unit = 30):
        subTransactions = self.transactions[self.transactions['Symbol'].isin(listSymbols)]
        buyTranactions = subTransactions[subTransactions['Amount ($)']<0]
        df = buyTranactions.copy()
        df['Days Held'] = (self.cob - df['Run Date']).apply(lambda x: x.days)
        df['Weight'] = df['Amount ($)'].abs()
        totalWeightedHold = (df['Days Held'] * df['Weight']).sum() / df['Weight'].sum()/ unit
        totalWeightedHoldRow = pd.DataFrame({'Symbol': ['Total'], 'Weighted Avg Holding Period': [totalWeightedHold]})

        # 分组计算加权平均
        weightedHold = (
            df.groupby('Symbol')
            .apply(lambda g: (g['Days Held'] * g['Weight']).sum() / g['Weight'].sum()/ unit, include_groups=False)
            .reset_index(name='Weighted Avg Holding Period')
        )
        
        weightedHold = pd.concat([weightedHold, totalWeightedHoldRow], ignore_index=True)
        return weightedHold
    
    
    def get_symbol_current_values(self, listSymbols: list):
        resultList = []
        totalCurrentValue = self.get_total_symbols_value(listSymbols)
        for symbol in listSymbols:
            currentValue = self.get_symbol_current_value(symbol)
            currentValuePercent = currentValue/totalCurrentValue
            resultList.append({
                'Symbol': symbol,
                'Current Value': currentValue,
                'Percentage': currentValuePercent
            })
        resultList.append({
                'Symbol': 'Total',
                'Current Value': totalCurrentValue,
                'Percentage': 1
            })
        return pd.DataFrame(resultList)
    
    def get_symbol_current_value(self,symbol):
        try:
            value = self.position.loc[self.position['Symbol']==symbol, 'Current Value'].values[0]
        except:
            value = 0
        return value
        
    def get_total_symbols_value(self, symbols: list):
        Position = self.individualPosition[self.individualPosition['Symbol'].isin(symbols)]
        totalValue = Position['Current Value'].sum()
        return totalValue
    
    def get_symbol_irrs(self, listSymbols: list):
        resultList = []
        for symbol in listSymbols:
            irr = self.get_combined_symbol_irr([symbol])
            resultList.append({
                'Symbol': symbol,
                'IRR': irr
            })
        totalIrr = self.get_combined_symbol_irr(listSymbols)
        resultList.append({
                'Symbol': 'Total',
                'IRR': totalIrr
            })
        return pd.DataFrame(resultList)
    
    def get_combined_symbol_irr(self, listSymbols: list):
        trans = self.transactions[self.transactions['Symbol'].isin(listSymbols)]
        cashflows = trans['Amount ($)'].tolist()
        dates = trans['Run Date'].tolist()
        current_value = self.position.loc[self.position['Symbol'].isin(listSymbols), 'Current Value'].sum()
        cashflows.append(current_value)
        dates.append(self.cob)
        irr = compute_irr(cashflows, dates, self.cob)
        return irr
    
    def get_stock_symbol_list(self):
        symbols = self.individualTransactions['Symbol'].unique()
        stockSymbols = [
            sym for sym in symbols
            if sym not in self.cashSymbols
            and not sym.startswith('91')
            and sym not in self.otherSymbols
        ]
        return stockSymbols
    
    def get_bond_symbol_list(self):
        symbols = self.individualTransactions['Symbol'].unique()
        bondSymbols = [
            sym for sym in symbols
            if  sym.startswith('91')
        ]
        return bondSymbols
    
    
# class Portfolio:
#     """
#     A class to represent a fidelity portfolio.

#     Attributes
#     ----------
#     transactions: pd.DataFrame
#         All historial transactions.
#     position: pd.DataFrame
#         Current balance in the account.
#     today: datetime.date
#         Today's date
#     individual_transactions: pd.DataFrame
#         Transactions under account "Individual Z23390746"
#     individual_position: pd.DataFrame
#         Position under account "Individual Z23390746"

#     Methods
#     -------
#     show_investment_distribution:
#         display the result of get_investment_distribution.
#     get_investment_distribution:
#         get the distribution of investment amony differnet asset.
#     get_total_investment:
#         get total investment amount in dollar.
#     get_stock_investment:
#         get amount of stock investment in dollar.
#     get_bill_investment:
#         get amount of bill investment in dollar.
#     get_other_investment:
#         get amount of other investment in dollar.
#     show_stock_irr:
#         display the result of get_stock_irr.
#     get_stock_irr:
#         get the irr of each stock.
#     add_total_current_value_to_individual_position:
#         ---
#     get_total_current_value:
#         ---
#     set_merged_individual_position_transaction:
#         merge individual_position and individual_transaction.
#     add_time_diff:
#         ---
#     calculate_irr(symbol_list, lower_bound=-0.999, upper_bound=5):
#         filter all transactions with symbol in symbol_list. Then calculate the irr of these transactions.
#     filter_merged_transactions_by_symbol(symbol_list):
#         filter all transactions with symbol in symbol_list.
#     """

#     def __init__(self, transactions, position):
#         self.transactions = transactions
#         self.position = position

#         account_number_dic = {
#             "Individual":'Z23390746',
#             "401k":'86964',
#             "HSA":'241802439',
#             "Cash":'Z06872898'
#         }
        
#         self.today = datetime.now().date()
#         self.individual_transactions = self.transactions[
#             self.transactions["Account Number"] == account_number_dic["Individual"]
#         ]
#         self.pension_transactions = self.transactions[
#             self.transactions["Account Number"] == account_number_dic["401k"]
#         ]
#         self.HSA_transactions = self.transactions[
#             self.transactions["Account Number"] == account_number_dic["HSA"]
#         ]
#         self.cash_transactions = self.transactions[
#             self.transactions["Account Number"] == account_number_dic["Cash"]
#         ]
        
#         self.individual_position = self.position[
#             self.position["Account Number"] == account_number_dic["Individual"]
#         ]
#         self.pension_position = self.position[
#             self.position["Account Number"] == account_number_dic["401k"]
#         ]
#         self.HSA_position = self.position[
#             self.position["Account Number"] == account_number_dic["HSA"]
#         ]
#         self.cash_position = self.position[
#             self.position["Account Number"] == account_number_dic["Cash"]
#         ]
        

#     def show_investment_distribution(self):
#         investment_distribution = self.get_investment_distribution()
#         investment_distribution["Percent"] = [
#             f"{x * 100:.2f}%" for x in investment_distribution["Percent"]
#         ]
#         print(pd.DataFrame(investment_distribution))

#     def get_investment_distribution(self):
#         total_investment = self.get_total_investment()
#         stock_investment = self.get_stock_investment()
#         bill_investment = self.get_bill_investment()
#         other_investment = self.get_other_investment()
#         result = {
#             "Class": ["stock", "bill", "other", "total"],
#             "Amount": [
#                 stock_investment,
#                 bill_investment,
#                 other_investment,
#                 total_investment,
#             ],
#             "Percent": [
#                 stock_investment / total_investment,
#                 bill_investment / total_investment,
#                 other_investment / total_investment,
#                 total_investment / total_investment,
#             ],
#         }

#         return result

#     def get_total_investment(self):
#         total_investment = self.individual_transactions[
#             self.individual_transactions["Symbol"] == "Transfer"
#         ]["Amount ($)"].sum()
#         return total_investment

#     def get_stock_investment(self):
#         stock_position = self.individual_position[
#             ~(self.individual_position["Description"] == "HELD IN MONEY MARKET")
#             & ~(self.individual_position["Description"].str.contains("BILLS", na=False))
#         ]
#         return stock_position["Cost Basis Total"].sum()

#     def get_bill_investment(self):
#         bill_position = self.individual_position[
#             (self.individual_position["Description"].str.contains("BILLS", na=False))
#         ]
#         return bill_position["Cost Basis Total"].sum()

#     def get_other_investment(self):
#         return (
#             self.get_total_investment()
#             - self.get_stock_investment()
#             - self.get_bill_investment()
#         )

#     def show_stock_irr(self):
#         stock_irr = self.get_stock_irr()
#         stock_irr_nice_look = pd.DataFrame(
#             {
#                 "Stock": stock_irr.keys(),
#                 "irr": [f"{(stock_irr[x]) * 100:.2f}%" for x in stock_irr.keys()],
#             }
#         )
#         print(pd.DataFrame(stock_irr_nice_look))

#     def get_stock_irr(self):
#         self.add_total_current_value_to_individual_position()
#         self.set_merged_individual_position_transaction()
#         self.merged_individual_position_transaction = self.add_time_diff(self.merged_individual_position_transaction)

#         unique_symbols = self.merged_individual_position_transaction["Symbol"].unique()
#         stock_list = [
#             element
#             for element in unique_symbols
#             if "FZFXX" not in element
#             and not element[0].isdigit()
#             and "Pending" not in element
#         ]
#         result_dict = {x: self.calculate_irr(self.filter_merged_transactions_by_symbol([x])) for x in stock_list}
#         if "Transfer" in stock_list:
#             stock_list.remove("Transfer")
#         transactions = self.filter_merged_transactions_by_symbol(stock_list)
#         result_dict["stock"] = self.calculate_irr(transactions)

#         return result_dict

#     def add_total_current_value_to_individual_position(self):
#         if "Transfer" in self.individual_position["Symbol"].values:
#             print("Total current value has been added")
#             return

#         total_current_value = self.get_total_current_value()
#         new_rows = pd.DataFrame(
#             {"Symbol": ["Transfer"], "Current Value": -total_current_value}
#         )
#         self.individual_position = pd.concat(
#             [self.individual_position, new_rows], ignore_index=True
#         )

#     def get_total_current_value(self):
#         return self.individual_position["Current Value"].sum()

#     def set_merged_individual_position_transaction(self):
#         new_rows = pd.DataFrame(
#             {
#                 "Run Date": [self.today] * len(self.individual_position),
#                 "Symbol": self.individual_position["Symbol"],
#                 "Amount ($)": self.individual_position["Current Value"],
#             }
#         )

#         self.merged_individual_position_transaction = pd.concat(
#             [self.individual_transactions, new_rows], ignore_index=True
#         )

#     def add_time_diff(self, transactions):
#         transactions_copy = transactions.copy()
#         if not 'time_diffs_in_year' in transactions_copy.columns:
#             transactions_copy.loc[:, "time_diffs_in_year"] = (
#                 self.today - transactions_copy.loc[:, "Run Date"]
#             ).apply(lambda x: x.days) / 365.25
#         else:
#             print("Column time_diffs_in_year exists")
#         return transactions_copy
        

#     def calculate_irr(self, transactions, lower_bound=-0.999, upper_bound=5):

#         def npv(rate):
#             return np.sum(
#                 transactions["Amount ($)"]
#                 * (1 + rate) ** transactions["time_diffs_in_year"]
#             )

#         result = root_scalar(npv, bracket=[lower_bound, upper_bound], method="bisect")

#         if result.converged:
#             return result.root
#         else:
#             raise ValueError(
#                 "No solution found for the rate that satisfies the equation."
#             )

#     def filter_merged_transactions_by_symbol(self, symbol_list):
#         return self.merged_individual_position_transaction[
#             self.merged_individual_position_transaction["Symbol"].isin(symbol_list)
#         ]
        
    