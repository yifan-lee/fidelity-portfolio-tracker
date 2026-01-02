import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import optimize





def parse_date(date_str):
    """Parse various date formats."""
    if pd.isna(date_str):
        return None
    try:
        return pd.to_datetime(date_str).normalize()
    except Exception:
        return None

















def categorize_asset(row):
    """
    Categorize asset into Stock, Bond, or Cash/MoneyMarket.
    """
    symbol = str(row['Symbol'])
    desc = str(row.get('Description', '')).upper()
    
    # Money Market Funds
    mmf_symbols = ['FZFXX', 'FDRXX', 'SPAXX', 'QUSBQ'] # QUSBQ is bank sweep
    if symbol in mmf_symbols or 'MONEY MARKET' in desc or 'CASH RESERVES' in desc or 'FDIC INSURED DEPOSIT' in desc:
        return 'Cash'
    
    # US Treasury Bills/Notes
    # CUSIPs usually 9 digits, often starting with 912...
    # Or description contains TREAS BILL
    if (len(symbol) >= 8 and symbol.startswith('912')) or 'TREAS BILL' in desc or 'TREASURY BILL' in desc:
        return 'Bond'
        
    # Default to Stock/ETF
    return 'Stock'

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


# --- Unified Analysis System ---

def filter_transactions(history_df, account_num=None, symbol=None):
    """Filter transactions by Account and/or Symbol."""
    df = history_df.copy()
    if account_num:
        df = df[df['Account Number'] == account_num]
    if symbol:
        df = df[df['Symbol'] == symbol]
    return df

def identify_funding_flow(row):
    """
    For Account Analysis:
    Identify if row is a funding event (Deposit/Withdrawal).
    Returns (is_funding, flow_amount)
    Flow convention: Deposit is Investment (Negative Flow), Withdrawal is Return (Positive Flow).
    Since Fidelity Deposit is (+), we return -1 * Amount.
    """
    action = str(row['Action']).upper()
    amount = row['Amount ($)']
    
    if pd.isna(amount) or amount == 0:
        return False, 0.0

    funding_patterns = ['ELECTRONIC FUNDS TRANSFER', 'CHECK RECEIVED', 'DEPOSIT', 'WIRE', 'BILL PAY', 'CONTRIB', 'PARTIC CONTR']
    exclude_patterns = ['DIVIDEND', 'INTEREST', 'REINVESTMENT', 'YOU BOUGHT', 'YOU SOLD', 'REDEMPTION', 'FEE', 'EXCHANGE', 'MARKET', 'CASH RESERVES', 'GAIN', 'LOSS']
    
    is_funding = False
    if any(p in action for p in funding_patterns):
        is_funding = True
    if any(p in action for p in exclude_patterns):
        is_funding = False
        
    if is_funding:
        return True, -1 * amount
    return False, 0.0

def build_cash_flows(transactions_df, mode='trade'):
    """
    Construct cash flow series from filtered transactions.
    mode='trade': All transactions are flows. Flow = Amount. (Symbol Analysis)
    mode='funding': Only funding transactions. Flow = -Amount. (Account Analysis)
    
    Returns: list of (date, flow), total_invested_basis
    """
    cash_flows = []
    total_invested = 0.0
    
    for _, row in transactions_df.iterrows():
        date = row['Run Date']
        amount = row['Amount ($)']
        
        if mode == 'funding':
            is_valid, flow = identify_funding_flow(row)
            if not is_valid:
                continue
        else:
            # Trade Mode: Flow is just the amount (Buy is -, Sell/Div is +)
            # Exception: "Contributions" in 401k are often positive amounts but represent investment (Buy).
            if 'CONTRIBUTION' in str(row['Action']).upper() and amount > 0:
                flow = -1 * amount
            else:
                flow = amount
            
        cash_flows.append((date, flow))
        
        # Track Invested Capital (Sum of negative flows)
        if flow < 0:
            total_invested += abs(flow)
            
    return cash_flows, total_invested

def calculate_metrics(cash_flows, current_value, latest_date, total_invested_basis):
    """
    Calculate generic metrics: IRR, Total Return $, ROI %.
    """
    # Append terminal value
    final_flows = cash_flows.copy()
    if current_value > 0:
        final_flows.append((latest_date, current_value))
        
    irr_val = xirr(final_flows)
    
    # Total Return $ = (Sum of Flows + Current Value)
    # Note: Flows includes the initial negative investments.
    # So Sum(Flows) is Net Realized PnL.
    # Adding Current Value gives Total PnL.
    # Wait, simple check: Invest -100. Current 110. Sum Flows = -100. Total PnL = -100 + 110 = 10. Correct.
    total_return_dollar = sum([f for _, f in cash_flows]) + current_value
    
    # ROI
    roi = (total_return_dollar / total_invested_basis) if total_invested_basis > 0 else 0.0
    
    return {
        'Total Invested': total_invested_basis,
        'Total Return ($)': total_return_dollar,
        'ROI': roi,
        'IRR': irr_val if irr_val is not None else 0.0
    }

def analyze_entity_performance(history_df, latest_date, current_value, account_num=None, symbol=None, mode='trade'):
    """
    Generic Entry Point for analyzing an entity (Account or Symbol).
    """
    # 1. Filter Transactions
    filtered_hist = filter_transactions(history_df, account_num, symbol)
    
    # 2. Build Cash Flows
    cash_flows, total_invested = build_cash_flows(filtered_hist, mode=mode)
    
    # 3. Calculate Metrics
    return calculate_metrics(cash_flows, current_value, latest_date, total_invested)

# --- Wrappers for backward compatibility / convenience ---

def analyze_symbol_performance(positions_df, history_df, latest_date):
    """Iterate positions and calculate performance using Unified System (mode='trade')."""
    results = []
    
    # Filter out Pending activity
    # Check both Account Name and Symbol just in case
    mask = (positions_df['Account Name'] != 'Pending activity') & (positions_df['Symbol'] != 'Pending activity')
    valid_positions = positions_df[mask]
    
    for _, row in valid_positions.iterrows():
        sym = row['Symbol']
        acc_num = row['Account Number']
        curr_val = row['Current Value']
        
        metrics = analyze_entity_performance(
            history_df, latest_date, curr_val, 
            account_num=acc_num, symbol=sym, mode='trade'
        )
        
        results.append({
            'Account Name': row['Account Name'],
            'Account Number': acc_num,
            'Symbol': sym,
            'Asset Type': categorize_asset(row),
            'Current Value': curr_val,
            'Total Invested': metrics['Total Invested'],
            'Total Return ($)': metrics['Total Return ($)'],
            'Total Return (%)': metrics['ROI'],
            'IRR': metrics['IRR']
        })
    return pd.DataFrame(results)

def analyze_account_performance(history_df, account_num, latest_date, current_account_value):
    """Analyze account using Unified System (mode='funding')."""
    return analyze_entity_performance(
        history_df, latest_date, current_account_value, 
        account_num=account_num, mode='funding'
    )
        
# Example usage block (not executed on import)
if __name__ == "__main__":
    pass
