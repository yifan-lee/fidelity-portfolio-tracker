from support_functions.analysis import load_data, categorize_asset, xirr
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

def analyze_symbol_performance(positions_df, history_df):
    """
    Calculate performance for each symbol in the current portfolio.
    """
    results = []
    
    # Identify unique (Account, Symbol) pairs in current positions
    # We only care about what we currently hold for the "Stock analysis" requirement?
    # Or everything we ever held? User asked: "All stocks bought in individual account".
    # Let's start with Current Positions + realized gains for completeness if possible, 
    # but based on requirements "Each stock in every account", likely implies current holdings or full history.
    # Let's drive it by Current Positions first, as that's where we have "Current Value".
    
    # If a stock is fully sold, it won't be in positions_df. 
    # To capture fully sold stocks, we'd need to interpret history unique symbols.
    # For now, let's focus on Active Positions as per typical portfolio trackers.
    
    for i, row in positions_df.iterrows():
        symbol = row['Symbol']
        account_num = row['Account Number']
        account_name = row['Account Name']
        current_val = row['Current Value']
        quantity = row['Quantity']
        asset_type = categorize_asset(row)
        
        # Filter History
        mask = (history_df['Account Number'] == account_num) & (history_df['Symbol'] == symbol)
        symbol_hist = history_df[mask]
        
        # Build Cash Flows
        cash_flows = []
        
        # 1. Transactions (Buys are negative amount, Sells/Divs are positive amount in Fidelity History)
        # Verify assumption:
        # Buy: Amount is negative (outflow).
        # Sell: Amount is positive (inflow).
        # Div: Amount is positive (inflow).
        # So we can sum 'Amount ($)' directly.
        
        relevant_actions = symbol_hist[symbol_hist['Amount ($)'].notna()]
        
        total_invested = 0
        total_returned = 0
        
        for _, h_row in relevant_actions.iterrows():
            date = h_row['Run Date']
            amt = h_row['Amount ($)']
            cash_flows.append((date, amt))
            
            if amt < 0:
                total_invested += abs(amt)
            else:
                total_returned += amt
                
        # 2. Add Current Value as a final "inflow" on today's date
        # Only if we currently hold it (Current Value > 0)
        today = datetime.now()
        if current_val > 0:
            cash_flows.append((today, current_val))
            
        # Metrics
        irr_val = xirr(cash_flows)
        
        # Total Return ($) = (Total Returned + Current Value) - Total Invested
        # Or simply Sum of all Cash Flows (since Flows include negative buys and positive sells/divs) + Current Value
        total_return_dollar = sum([cf[1] for cf in cash_flows]) # Note: cash_flows includes Current Value now
        
        # Return % = Total Return $ / Total Invested 
        # (Simple ROI, distinct from IRR)
        total_return_pct = (total_return_dollar / total_invested) if total_invested > 0 else 0
        
        results.append({
            'Account Name': account_name,
            'Account Number': account_num,
            'Symbol': symbol,
            'Asset Type': asset_type,
            'Current Value': current_val,
            'Total Invested': total_invested,
            'Total Return ($)': total_return_dollar,
            'Total Return (%)': total_return_pct,
            'IRR': irr_val if irr_val is not None else np.nan
        })
        
    return pd.DataFrame(results)

def main():
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    positions_df, history_df = load_data(data_dir)
    
    print("\n" + "="*50)
    print("FIDELITY PORTFOLIO ANALYSIS")
    print("="*50)
    
    # 1. Total Portfolio Performance
    total_value = positions_df['Current Value'].sum()
    print(f"\n[1] Total Portfolio Value: ${total_value:,.2f}")
    
    # For Portfolio IRR, we need aggregate cash flows of the ENTIRE set of accounts.
    # Cash Flow = External Inflows/Outflows.
    # Identifying External Flows in Fidelity CSV is tricky (Action descriptions vary).
    # Heuristic: 'Electronic Funds Transfer', 'Check', 'Deposit', 'Withdrawal'.
    # EXCLUDING: 'Reinvestment', 'Dividend', 'Buy', 'Sell', 'Interest'.
    
    # Let's try to calculate per-position metrics first and aggregate them? 
    # No, IRR doesn't aggregate linearly.
    
    # Let's generate the detailed table first (Requirement #3 & #4)
    print("\nCalculating performance for all positions...")
    perf_df = analyze_symbol_performance(positions_df, history_df)
    
    # Fill NaNs for display
    perf_df['IRR'] = perf_df['IRR'].fillna(0.0)
    
    # Requirement #3: Each Account -> Each Stock
    # We already have this in perf_df (Account, Symbol).
    # Let's print it nicely.
    
    print("\n[3] Performance by Account & Symbol:")
    accounts = perf_df['Account Name'].unique()
    for acct in accounts:
        print(f"\n--- Account: {acct} ---")
        acct_df = perf_df[perf_df['Account Name'] == acct].sort_values('Current Value', ascending=False)
        
        # Calculate Account Total Weighted
        acct_val = acct_df['Current Value'].sum()
        acct_return_dollar = acct_df['Total Return ($)'].sum()
        acct_invested = acct_df['Total Invested'].sum()
        acct_roi = (acct_return_dollar / acct_invested) if acct_invested > 0 else 0
        
        print(f"{'Symbol':<10} {'Type':<6} {'Value':<12} {'Return($)':<12} {'Return(%)':<10} {'IRR':<8} {'Alloc(%)':<6}")
        for _, row in acct_df.iterrows():
            alloc = (row['Current Value'] / acct_val) * 100 if acct_val > 0 else 0
            print(f"{row['Symbol']:<10} {row['Asset Type']:<6} ${row['Current Value']:<11,.2f} ${row['Total Return ($)']:<11,.2f} {row['Total Return (%)']*100:>8.2f}% {row['IRR']*100:>7.2f}% {alloc:>7.2f}%")
            
        print(f"{'TOTAL':<10} {'-':<6} ${acct_val:<11,.2f} ${acct_return_dollar:<11,.2f} {acct_roi*100:>8.2f}% {'--':>8} {'100.00':>7}%")


    # Requirement #4: Stock vs Bond vs Cash Aggregates
    print("\n[4] Performance by Asset Class:")
    type_groups = perf_df.groupby('Asset Type').agg({
        'Current Value': 'sum',
        'Total Invested': 'sum',
        'Total Return ($)': 'sum'
    }).reset_index()
    
    type_groups['Return (%)'] = type_groups.apply(lambda x: (x['Total Return ($)'] / x['Total Invested']) if x['Total Invested'] > 0 else 0, axis=1)
    type_groups['Allocation (%)'] = (type_groups['Current Value'] / total_value) * 100
    
    print(f"{'Type':<10} {'Value':<15} {'Return($)':<15} {'Return(%)':<10} {'Alloc(%)':<10}")
    for _, row in type_groups.iterrows():
        print(f"{row['Asset Type']:<10} ${row['Current Value']:<14,.2f} ${row['Total Return ($)']:<14,.2f} {row['Return (%)']*100:>8.2f}% {row['Allocation (%)']:>8.2f}%")


if __name__ == "__main__":
    main()
