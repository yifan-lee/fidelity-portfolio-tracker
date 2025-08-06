from datetime import datetime,date
import pandas as pd
import numpy as np
from support_functions.compute_irr import compute_irr

class Portfolio:
    def __init__(self, transactions, position):
        self.transactions = transactions
        self.position = position
        self.cob = date.today()
        
        self.account_number_dic = {
            "Individual":'Z23390746',
            "401k":'86964',
            "HSA":'241802439',
            "Cash":'Z06872898'
        }
        
        self.pensionTransactions = transactions[transactions['Account Number']==self.account_number_dic["401k"]]
        self.pensionPosition = position[position['Account Number']==self.account_number_dic["401k"]]
        self.HSATransactions = transactions[transactions['Account Number']==self.account_number_dic["HSA"]]
        self.HSAPosition = position[position['Account Number']==self.account_number_dic["HSA"]]
        self.cashTransactions = transactions[transactions['Account Number']==self.account_number_dic["Cash"]]
        self.cashPosition = position[position['Account Number']==self.account_number_dic["Cash"]]
        
        
        self.cashSymbols = ['FZFXX**','FZFXX']
        self.otherSymbols = ['Pending Activity']
        self.contributionSymbols = ['','Transfer']
        self.bondSymbols = self.get_bond_symbol_list()
        self.stockSymbols = self.get_stock_symbol_list()
        
        self.cashDescriptions = ['HELD IN MONEY MARKET','FIDELITY TREASURY MONEY MARKET FUND']
        self.otherDescriptions = []
        self.contributionDescriptions = ['No Description']
        self.bondDescriptions = self.get_bond_description_list()
        self.stockDescriptions = self.get_stock_description_list()
        
    ## Main functions
    
    def get_account_summary(self):
        colName = 'Symbol'
        totalValueBond, totalIrrBond, holdingPeriodBond = self.get_combined_bond_result(colName)
        totalValueSymbol, totalIrrSymbol, holdingPeriodSymbol = self.get_combined_stock_result(colName)
        totalValueCash, totalIrrCash, holdingPeriodCash = self.get_combined_cash_result(colName)
        
        
        totalIRR = self.get_total_irr(colName)
        totalValue = self.position['Current Value'].sum()
        totalHoldingPeriod = (totalValueBond*holdingPeriodBond+totalValueSymbol*holdingPeriodSymbol+totalValueCash*holdingPeriodCash)/(totalValueBond+totalValueSymbol+totalValueCash)
        
        
        result = pd.DataFrame({
            'Type':['bond','stock','cash','Total'],
            'Value': [totalValueBond,totalValueSymbol,totalValueCash,totalValue],
            'Percentage':[totalValueBond,totalValueSymbol,totalValueCash,totalValue]/totalValue,
            'IRR':[totalIrrBond, totalIrrSymbol, totalIrrCash,totalIRR],
            'Weighted Avg Holding Period':[holdingPeriodBond,holdingPeriodSymbol,holdingPeriodCash,totalHoldingPeriod]
        } 
        )
        return result
    
    def get_all_bond_summary(self, colName='Symbol',showExpiredBond=False):
        listKeys = self.get_bond_key_list(colName)
        currentValueResult = self.get_key_current_values(listKeys,colName)
        irrResult = self.get_key_irrs(listKeys,colName)
        holdingPeriodResult = self.get_key_holding_period(listKeys,colName)
        result = pd.merge(currentValueResult, irrResult, on=colName)
        result = pd.merge(result, holdingPeriodResult, on=colName)
        result = result.sort_values(by='Current Value', ascending=False)
        if not showExpiredBond:
            result = result[result['Current Value']>0]
        return result
        
    def get_all_stock_summary(self, colName='Symbol'):
        listKeys = self.get_stock_key_list(colName)
        currentValueResult = self.get_key_current_values(listKeys,colName)
        irrResult = self.get_key_irrs(listKeys,colName)
        holdingPeriodResult = self.get_key_holding_period(listKeys,colName)
        result = pd.merge(currentValueResult, irrResult, on=colName)
        result = pd.merge(result, holdingPeriodResult, on=colName)
        result = result.sort_values(by='Current Value', ascending=False)
        return result
    
    
    
    
    ## Help functions
    
    def get_combined_bond_result(self, colName):
        listKeys = self.get_bond_key_list(colName)
        totalValue = self.get_total_keys_value(listKeys,colName)
        totalIrr = self.get_combined_key_irr(listKeys,colName)
        holdingPeriod = self.get_combined_key_holding_period(listKeys,colName)
        return totalValue, totalIrr, holdingPeriod
    
    def get_combined_stock_result(self, colName):
        listKeys = self.get_stock_key_list(colName)
        totalValue = self.get_total_keys_value(listKeys,colName)
        totalIrr = self.get_combined_key_irr(listKeys,colName)
        holdingPeriod = self.get_combined_key_holding_period(listKeys,colName)
        return totalValue, totalIrr, holdingPeriod
    
    def get_combined_cash_result(self, colName):
        listKeys = self.get_cash_key_list(colName)
        totalValue = self.get_total_keys_value(listKeys,colName)
        totalIrr = self.get_combined_key_irr(listKeys,colName)
        holdingPeriod = self.get_combined_key_holding_period(listKeys,colName)
        return totalValue, totalIrr, holdingPeriod
    
    
    
    
    def get_combined_key_holding_period(self, listKeys: list, colName, unit = 30):
        subTransactions = self.transactions[self.transactions[colName].isin(listKeys)]
        buyTranactions = subTransactions[subTransactions['Amount ($)']<0]
        df = buyTranactions.copy()
        df['Days Held'] = (self.cob - df['Run Date']).apply(lambda x: x.days)
        df['Weight'] = df['Amount ($)'].abs()
        totalWeightedHold = (df['Days Held'] * df['Weight']).sum() / df['Weight'].sum()/ unit
        return totalWeightedHold
        
    def get_key_holding_period(self, listKeys: list, colName, unit = 30):
        subTransactions = self.transactions[self.transactions[colName].isin(listKeys)]
        buyTranactions = subTransactions[subTransactions['Amount ($)']<0]
        df = buyTranactions.copy()
        df['Days Held'] = (self.cob - df['Run Date']).apply(lambda x: x.days)
        df['Weight'] = df['Amount ($)'].abs()
        totalWeightedHold = (df['Days Held'] * df['Weight']).sum() / df['Weight'].sum()/ unit
        totalWeightedHoldRow = pd.DataFrame({colName: ['Total'], 'Weighted Avg Holding Period': [totalWeightedHold]})

        # 分组计算加权平均
        weightedHold = (
            df.groupby(colName)
            .apply(lambda g: (g['Days Held'] * g['Weight']).sum() / g['Weight'].sum()/ unit, include_groups=False)
            .reset_index(name='Weighted Avg Holding Period')
        )
        
        weightedHold = pd.concat([weightedHold, totalWeightedHoldRow], ignore_index=True)
        return weightedHold
    
    
    def get_key_current_values(self, listKeys: list, colName):
        resultList = []
        totalCurrentValue = self.get_total_keys_value(listKeys, colName)
        for key in listKeys:
            currentValue = self.get_key_current_value(key, colName)
            currentValuePercent = currentValue/totalCurrentValue
            resultList.append({
                colName: key,
                'Current Value': currentValue,
                'Percentage': currentValuePercent
            })
        resultList.append({
                colName: 'Total',
                'Current Value': totalCurrentValue,
                'Percentage': 1
            })
        return pd.DataFrame(resultList)
    
    def get_key_current_value(self,key, colName):
        try:
            value = self.position.loc[self.position[colName]==key, 'Current Value'].values[0]
        except:
            value = 0
        return value
        
    def get_total_keys_value(self, listKeys: list, colName):
        Position = self.position[self.position[colName].isin(listKeys)]
        totalValue = Position['Current Value'].sum()
        return totalValue
    
    def get_key_irrs(self, listKeys: list, colName):
        resultList = []
        for key in listKeys:
            irr = self.get_combined_key_irr([key], colName)
            resultList.append({
                colName: key,
                'IRR': irr
            })
        totalIrr = self.get_combined_key_irr(listKeys, colName)
        resultList.append({
                colName: 'Total',
                'IRR': totalIrr
            })
        return pd.DataFrame(resultList)
    
    def get_total_irr(self, colName):
        if colName == 'Symbol':
            contributionKeys = self.contributionSymbols
        elif colName == 'Description':
            contributionKeys = self.contributionDescriptions
        else:
            return 0
        trans = self.transactions[self.transactions[colName].isin(contributionKeys)]
        cashflows = trans['Amount ($)'].tolist()
        cashflows = [-x for x in cashflows]
        dates = trans['Run Date'].tolist()
        current_value = self.position['Current Value'].sum()
        cashflows.append(current_value)
        dates.append(self.cob)
        irr = compute_irr(cashflows, dates, self.cob)
        return irr
    
    
    def get_combined_key_irr(self, listKeys: list, colName):
        trans = self.transactions[self.transactions[colName].isin(listKeys)]
        cashflows = trans['Amount ($)'].tolist()
        dates = trans['Run Date'].tolist()
        current_value = self.position.loc[self.position[colName].isin(listKeys), 'Current Value'].sum()
        cashflows.append(current_value)
        dates.append(self.cob)
        irr = compute_irr(cashflows, dates, self.cob)
        return irr
    
    
    def get_stock_key_list(self, colName='Description'):
        if colName == 'Symbol':
            listKeys = self.get_stock_symbol_list()
        elif colName == 'Description':
            listKeys = self.get_stock_description_list()
        else:
            listKeys = []
        return listKeys
    
    def get_stock_symbol_list(self):
        symbols = self.transactions['Symbol'].unique()
        stockSymbols = [
            sym for sym in symbols
            if sym not in self.cashSymbols
            and not str(sym).startswith('91')
            and sym not in self.otherSymbols
            and sym not in self.contributionSymbols
        ]
        return stockSymbols
    
    def get_stock_description_list(self):
        descriptions = self.transactions['Description'].unique()
        stockDescriptions = [
            desc for desc in descriptions
            if desc not in self.cashDescriptions
            and not str(desc).startswith('UNITED STATES TREAS BILLS')
            and desc not in self.otherDescriptions
            and desc not in self.contributionDescriptions
        ]
        return stockDescriptions
    
    def get_bond_key_list(self, colName='Description'):
        if colName == 'Symbol':
            listKeys = self.get_bond_symbol_list()
        elif colName == 'Description':
            listKeys = self.get_bond_description_list()
        else:
            listKeys = []
        return listKeys
    
    def get_bond_symbol_list(self):
        symbols = self.transactions['Symbol'].unique()
        bondSymbols = [
            sym for sym in symbols
            if  str(sym).startswith('91')
        ]
        return bondSymbols
    
    def get_bond_description_list(self):
        descriptions = self.transactions['Description'].unique()
        bondDescriptions = [
            desc for desc in descriptions
            if  str(desc).startswith('UNITED STATES TREAS BILLS')
        ]
        return bondDescriptions
    
    
    
    def get_cash_key_list(self, colName):
        if colName == 'Symbol':
            listKeys = self.cashSymbols
        elif colName == 'Description':
            listKeys = self.cashDescriptions
        else:
            listKeys = []
        return listKeys
    
    def get_401k_description_list(self):
        descriptions = self.pensionTransactions['Description'].unique()
        return descriptions
    


class IndividualPortfolio(Portfolio):
    ## BBRK's description is different for trans and posi
    def __init__(self, transactions, position):
        super().__init__(transactions, position)
        self.transactions = transactions[transactions['Account Number']==self.account_number_dic["Individual"]]
        self.position = position[position['Account Number']==self.account_number_dic["Individual"]]
        
        
        
class PensionPortfolio(Portfolio):
    def __init__(self, transactions, position):
        super().__init__(transactions, position)
        self.transactions = transactions[transactions['Account Number']==self.account_number_dic["401k"]]
        self.position = position[position['Account Number']==self.account_number_dic["401k"]]
        
    def get_combined_key_irr(self, listKeys: list, colName):
        trans = self.transactions[self.transactions[colName].isin(listKeys)]
        cashflows = trans['Amount ($)'].tolist()
        cashflows = [-x for x in cashflows]
        dates = trans['Run Date'].tolist()
        current_value = self.position.loc[self.position[colName].isin(listKeys), 'Current Value'].sum()
        cashflows.append(current_value)
        dates.append(self.cob)
        irr = compute_irr(cashflows, dates, self.cob)
        return irr
    