import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple
import pandas as pd

from support_functions.data_loader import load_data


@dataclass
class EntityCashFlows:
    cash_flows: List[Tuple[datetime.datetime, float]]
    total_invested: float
    current_value: float
    latest_date: datetime.datetime


def filter_stock_transactions(transactions_df, account_num, symbol):
    df = transactions_df.copy()
    df = df[
        (df['Account Number'] == account_num) &
        (df['Symbol'] == symbol)
    ]
    return df
    
def filter_account_transactions(transactions_df, account_num):
    df = transactions_df.copy()
    funding_patterns = [
        'ELECTRONIC FUNDS TRANSFER', 'CHECK RECEIVED', 'DEPOSIT', 'WIRE', 
        'BILL PAY', 'CONTRIB', 'PARTIC CONTR'
    ]
    mask_account = (df['Account Number'] == account_num)
    mask_pattern = df['Action'].str.upper().apply(lambda x: any(p in str(x) for p in funding_patterns))
    
    df = df[mask_account & mask_pattern]
    return df

def filter_stock_positions(positions_df, account_num, symbol):
    df = positions_df.copy()
    df = df[
        (df['Account Number'] == account_num) &
        (df['Symbol'] == symbol)
    ]
    return df

def filter_account_positions(positions_df, account_num):
    df = positions_df.copy()
    df = df[df['Account Number'] == account_num]
    return df


def build_stock_cash_flows(data, account_num, symbol):
    transactions_df = data.transactions
    positions_df = data.positions
    latest_date = data.latest_date
    
    filtered_hist = filter_stock_transactions(transactions_df, account_num, symbol)
    filtered_posi = filter_stock_positions(positions_df, account_num, symbol)

    cash_flows = []
    total_invested = 0.0
    current_val = filtered_posi['Current Value'].iloc[0]
    for _, row in filtered_hist.iterrows():
        date = row['Run Date']
        amount = row['Amount ($)']
        flow = amount
        cash_flows.append((date, flow))
        
        # Track Invested Capital (Sum of negative flows)
        if flow < 0:
            total_invested += abs(flow)

    cash_flows.append((latest_date, current_val))
    return EntityCashFlows(
        cash_flows=cash_flows, 
        total_invested=total_invested, 
        current_value=current_val,
        latest_date=latest_date
    )
    
    
def build_account_cash_flows(data, account_num):
    transactions_df = data.transactions
    positions_df = data.positions
    latest_date = data.latest_date
    
    if account_num == 'Z06872898':
        cash_flows = []
        filtered_posi = filter_account_positions(positions_df, account_num)
        initial_date = pd.to_datetime('2022-07-26')
        current_val = filtered_posi['Current Value'].iloc[0]
        cash_flows.append((initial_date, -100))
        cash_flows.append((latest_date, current_val))
        return EntityCashFlows(
            cash_flows=cash_flows, 
            total_invested=100, 
            current_value=current_val,
            latest_date=latest_date
        )
    filtered_hist = filter_account_transactions(transactions_df, account_num)
    filtered_posi = filter_account_positions(positions_df, account_num)

    cash_flows = []
    total_invested = 0.0
    current_val = filtered_posi['Current Value'].sum()
    for _, row in filtered_hist.iterrows():
        date = row['Run Date']
        amount = row['Amount ($)']
        flow = -amount
        cash_flows.append((date, flow))
        
        # Track Invested Capital (Sum of negative flows)
        total_invested -= (flow)

    cash_flows.append((latest_date, current_val))
    return EntityCashFlows(
        cash_flows=cash_flows, 
        total_invested=total_invested, 
        current_value=current_val,
        latest_date=latest_date
    )
    

if __name__ == "__main__":
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    output_dir = f'{project_path}/output'

    data = load_data(data_dir)

    account = 'Z23390746'
    symbol = 'AAPL'
    entity_cash_flows = build_stock_cash_flows(data, account, symbol)
    print(f"Total invested of {account} {symbol}: {entity_cash_flows.total_invested}")
    print(f"Current value of {account} {symbol}: {entity_cash_flows.current_value}")

    account = 'Z23390746'
    entity_cash_flows = build_account_cash_flows(data, account)
    print(f"Total invested of {account}: {entity_cash_flows.total_invested}")
    print(f"Current value of {account}: {entity_cash_flows.current_value}")

    account = '241802439'
    entity_cash_flows = build_account_cash_flows(data, account)
    print(f"Total invested of {account}: {entity_cash_flows.total_invested}")
    print(f"Current value of {account}: {entity_cash_flows.current_value}")

    account = '86964'
    entity_cash_flows = build_account_cash_flows(data, account)
    print(f"Total invested of {account}: {entity_cash_flows.total_invested}")
    print(f"Current value of {account}: {entity_cash_flows.current_value}")

    account = 'Z06872898'
    entity_cash_flows = build_account_cash_flows(data, account)
    print(f"Total invested of {account}: {entity_cash_flows.total_invested}")
    print(f"Current value of {account}: {entity_cash_flows.current_value}")
