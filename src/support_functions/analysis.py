import pandas as pd
import numpy as np
from scipy import optimize


## Presentation Layer

def analyze_total_performance(positions_df, transactions_df, latest_date):
    accounts_unique = positions_df.groupby(['Account Number','Account Name'])['Current Value'].sum().reset_index()
    total_cash_flows = []
    total_invested = 0
    total_val = 0
    for _, row in accounts_unique.iterrows():
        acc_num = row['Account Number']
        curr_val = row['Current Value']
        cash_flows, curr_invested, curr_val = build_account_cash_flows(transactions_df, positions_df, latest_date, acc_num)
        total_val += curr_val
        total_invested += curr_invested
        total_cash_flows.extend(cash_flows)
    irr = xirr(total_cash_flows)
    total_return = total_val-total_invested
    total_return_ratio = total_return/total_invested
    result = [{
        'Account Name': None,
        'Account Number': None,
        'Symbol': None,
        'Asset Type': 'All',
        'Current Value': total_val,
        'Total Invested': total_invested,
        'Total Return ($)': total_return,
        'Total Return (%)': f"{total_return_ratio:.2%}",
        'IRR': f"{irr:.2%}" if irr is not None else "N/A",
        'Investment Ratio': "100%"
    }]
    return pd.DataFrame(result)
    

def analyze_account_performance(positions_df, transactions_df, latest_date):
    """Iterate positions and calculate performance using Unified System (mode='trade')."""
    results = []
    
    accounts_unique = positions_df.groupby(['Account Number','Account Name'])['Current Value'].sum().reset_index()
    
    for _, row in accounts_unique.iterrows():
        acc_num = row['Account Number']
        acc_name = row['Account Name']
        curr_val = row['Current Value']

        # if acc_name in ['ERNST & YOUNG 401(K)', 'Cash Management (Individual)']:
        #     continue
        
        total_invested, irr = analyze_entity_performance(transactions_df, positions_df, latest_date, account_num=acc_num, symbol=None)
        total_return = curr_val-total_invested
        total_return_ratio = total_return/total_invested
        
        results.append({
            'Account Name': acc_name,
            'Account Number': acc_num,
            'Symbol': None,
            'Asset Type': 'Account',
            'Current Value': curr_val,
            'Total Invested': total_invested,
            'Total Return ($)': total_return,
            'Total Return (%)': f"{total_return_ratio:.2%}",
            'IRR': f"{irr:.2%}" if irr is not None else "N/A"
        })
    results = pd.DataFrame(results)
    ratio = results['Total Invested'] / results['Total Invested'].sum()
    results['Investment Ratio'] = ratio.apply(lambda x: f"{x:.2%}")
    return results.sort_values('Total Invested', ascending=False)

def analyze_stock_performance(positions_df, transactions_df, latest_date):
    results = []

    accounts_unique = positions_df.groupby(['Account Number','Account Name'])['Current Value'].sum().reset_index()

    for _, row in accounts_unique.iterrows():
        
        acc_num = row['Account Number']
        acc_name = row['Account Name']

        if acc_name in ['ERNST & YOUNG 401(K)', 'Cash Management (Individual)','Health Savings Account']:
            continue
        
        target_type = 'Stock'
        sub_positions_df = positions_df[
            (positions_df['Account Name'] == acc_name) &
            (positions_df['Asset Type'] == target_type)
        ]

        for _, sub_row in sub_positions_df.iterrows():
            symbol = sub_row['Symbol']
            curr_val = sub_row['Current Value']
            if symbol in ['Pending activity']:
                continue
        
            total_invested, irr = analyze_entity_performance(transactions_df, positions_df, latest_date, account_num=acc_num, symbol=symbol)
            if total_invested > 0:
                total_return = curr_val - total_invested
                total_return_ratio = total_return / total_invested
            else:
                total_return = 0
                total_return_ratio = 0
                
            results.append({
                'Account Name': acc_name,
                'Account Number': acc_num,
                'Symbol': symbol,
                'Asset Type': 'Stock',
                'Current Value': curr_val,
                'Total Invested': total_invested,
                'Total Return ($)': total_return,
                'Total Return (%)': f"{total_return_ratio:.2%}",
                'IRR': f"{irr:.2%}" if irr is not None else "N/A"
            })
    results = pd.DataFrame(results)
    ratio = results['Total Invested'] / results['Total Invested'].sum()
    results['Investment Ratio'] = ratio.apply(lambda x: f"{x:.2%}")
    return results.sort_values('Total Invested', ascending=False)

            


        



## Math Core Layer

def calculate_metrics(cash_flows, current_value, total_invested):
    irr_val = xirr(cash_flows)
    total_return_dollar = current_value - total_invested
    roi = total_return_dollar / total_invested if total_invested != 0 else 0
    
    return {
        'IRR': irr_val,
        'Total Return ($)': total_return_dollar,
        'ROI': roi
    }


def xirr(cash_flows):
    """
    Calculate Internal Rate of Return (XIRR).
    cash_flows: List of (date, amount) tuples.
    """
    if not cash_flows or len(cash_flows) < 2:
        return None
        
    dates, amounts = width = zip(*cash_flows)
    
    # Convert dates to days from start
    min_date = min(dates)
    days = [(d - min_date).days for d in dates]
    
    # Optimization function
    def npv(r):
        arr = np.array(days)
        vals = np.array(amounts)
        return np.sum(vals / (1 + r)**(arr / 365.0))
        
    # Check signs
    pos = any(a > 0 for a in amounts)
    neg = any(a < 0 for a in amounts)
    if not (pos and neg):
        return None # Can't calculate IRR without both inflows and outflows
        
    try:
        res = optimize.newton(npv, 0.1, maxiter=50) # start guess at 10%
        return res
    except RuntimeError:
        return None


## Business Logic Layer


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


def build_stock_cash_flows(transactions_df, positions_df, latest_date, account_num, symbol):
        
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
    return cash_flows, total_invested, current_val
    
    
def build_account_cash_flows(transactions_df, positions_df, latest_date, account_num):
    symbol = None
    if account_num == 'Z06872898':
        cash_flows = []
        filtered_posi = filter_account_positions(positions_df, account_num, symbol)
        initial_date = pd.to_datetime('2022-07-26')
        current_val = filtered_posi['Current Value'].iloc[0]
        cash_flows.append((initial_date, -100))
        cash_flows.append((latest_date, current_val))
        return cash_flows, 100
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
    return cash_flows, total_invested, current_val
    




        
# Example usage block (not executed on import)
if __name__ == "__main__":
    pass
