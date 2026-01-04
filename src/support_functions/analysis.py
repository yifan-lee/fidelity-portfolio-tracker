import pandas as pd
import numpy as np
from scipy import optimize


def analyze_account_performance(positions_df, transactions_df, latest_date):
    """Iterate positions and calculate performance using Unified System (mode='trade')."""
    results = []
    
    accounts_unique = positions_df.groupby(['Account Number','Account Name'])['Current Value'].sum().reset_index()
    
    for _, row in accounts_unique.iterrows():
        acc_num = row['Account Number']
        acc_name = row['Account Name']
        curr_val = row['Current Value']

        if acc_name in ['ERNST & YOUNG 401(K)', 'Cash Management (Individual)']:
            continue
        
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
    return pd.DataFrame(results).sort_values('Total Return ($)', ascending=False)

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
    return pd.DataFrame(results).sort_values('Total Return ($)', ascending=False)

            


        

def analyze_entity_performance(transactions_df, positions_df, latest_date, account_num=None, symbol=None):
    """
    Generic Entry Point for analyzing an entity (Account or Symbol).
    """
    if symbol:
        cash_flows, total_invested = build_stock_cash_flows(transactions_df, positions_df, latest_date, account_num,symbol)
    else:
        cash_flows, total_invested = build_account_cash_flows(transactions_df, positions_df, latest_date, account_num)
    
    irr = xirr(cash_flows)
    
    # 3. Calculate Metrics
    return total_invested, irr

def filter_transactions(transactions_df, account_num=None, symbol=None):
    """Filter transactions by Account and/or Symbol."""
    df = transactions_df.copy()
    if symbol:
        df = df[
            (df['Account Number'] == account_num) &
            (df['Symbol'] == symbol)
        ]
    else:
        funding_patterns = [
            'ELECTRONIC FUNDS TRANSFER', 'CHECK RECEIVED', 'DEPOSIT', 'WIRE', 
            'BILL PAY', 'CONTRIB', 'PARTIC CONTR'
        ]
        mask_account = (df['Account Number'] == account_num)
        mask_pattern = df['Action'].str.upper().apply(lambda x: any(p in str(x) for p in funding_patterns))
        
        df = df[mask_account & mask_pattern]
    return df

def filter_positions(positions_df, account_num=None, symbol=None):
    """Filter positions by Account and/or Symbol."""
    df = positions_df.copy()
    if symbol:
        df = df[
            (df['Account Number'] == account_num) &
            (df['Symbol'] == symbol)
        ]
    else:
        df = df[df['Account Number'] == account_num]
    return df


def build_stock_cash_flows(transactions_df, positions_df, latest_date, account_num, symbol):
    if account_num == 'Z06872898':
        cash_flows = []
        filtered_posi = filter_positions(positions_df, account_num, symbol)
        initial_date = pd.to_datetime('2022-07-26')
        current_val = filtered_posi['Current Value'].iloc[0]
        cash_flows.append((initial_date, -100))
        cash_flows.append((latest_date, current_val))
        return cash_flows, current_val
        
    filtered_hist = filter_transactions(transactions_df, account_num, symbol)
    filtered_posi = filter_positions(positions_df, account_num, symbol)

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
    return cash_flows, total_invested
    
    
def build_account_cash_flows(transactions_df, positions_df, latest_date, account_num):
    symbol = None
    filtered_hist = filter_transactions(transactions_df, account_num, symbol)
    filtered_posi = filter_positions(positions_df, account_num, symbol)

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
    return cash_flows, total_invested
    


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


# # --- Unified Analysis System ---



# def identify_funding_flow(row):
#     """
#     For Account Analysis:
#     Identify if row is a funding event (Deposit/Withdrawal).
#     Returns (is_funding, flow_amount)
#     Flow convention: Deposit is Investment (Negative Flow), Withdrawal is Return (Positive Flow).
#     Since Fidelity Deposit is (+), we return -1 * Amount.
#     """
#     action = str(row['Action']).upper()
#     amount = row['Amount ($)']
    
#     if pd.isna(amount) or amount == 0:
#         return False, 0.0

#     funding_patterns = ['ELECTRONIC FUNDS TRANSFER', 'CHECK RECEIVED', 'DEPOSIT', 'WIRE', 'BILL PAY', 'CONTRIB', 'PARTIC CONTR']
#     exclude_patterns = ['DIVIDEND', 'INTEREST', 'REINVESTMENT', 'YOU BOUGHT', 'YOU SOLD', 'REDEMPTION', 'FEE', 'EXCHANGE', 'MARKET', 'CASH RESERVES', 'GAIN', 'LOSS']
    
#     is_funding = False
#     if any(p in action for p in funding_patterns):
#         is_funding = True
#     if any(p in action for p in exclude_patterns):
#         is_funding = False
        
#     if is_funding:
#         return True, -1 * amount
#     return False, 0.0



# def calculate_metrics(cash_flows, current_value, latest_date, total_invested_basis):
#     """
#     Calculate generic metrics: IRR, Total Return $, ROI %.
#     """
#     # Append terminal value
#     final_flows = cash_flows.copy()
#     if current_value > 0:
#         final_flows.append((latest_date, current_value))
        
#     irr_val = xirr(final_flows)
    
#     # Total Return $ = (Sum of Flows + Current Value)
#     # Note: Flows includes the initial negative investments.
#     # So Sum(Flows) is Net Realized PnL.
#     # Adding Current Value gives Total PnL.
#     # Wait, simple check: Invest -100. Current 110. Sum Flows = -100. Total PnL = -100 + 110 = 10. Correct.
#     total_return_dollar = sum([f for _, f in cash_flows]) + current_value
    
#     # ROI
#     roi = (total_return_dollar / total_invested_basis) if total_invested_basis > 0 else 0.0
    
#     return {
#         'Total Invested': total_invested_basis,
#         'Total Return ($)': total_return_dollar,
#         'ROI': roi,
#         'IRR': irr_val if irr_val is not None else 0.0
#     }


# --- Wrappers for backward compatibility / convenience ---



# def analyze_account_performance(history_df, account_num, latest_date, current_account_value):
#     """Analyze account using Unified System (mode='funding')."""
#     return analyze_entity_performance(
#         history_df, latest_date, current_account_value, 
#         account_num=account_num, mode='funding'
#     )
        
# Example usage block (not executed on import)
if __name__ == "__main__":
    pass
