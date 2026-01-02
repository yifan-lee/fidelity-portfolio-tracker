from support_functions.analysis import (
    load_data,
    analyze_symbol_performance
)
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path


def main():
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    positions_df, history_df, latest_date = load_data(data_dir)
    
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
    perf_df = analyze_symbol_performance(positions_df, history_df, latest_date)
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
        
        # Use new Account Analysis for Total Invested & IRR (Funding based)
        from support_functions.analysis import analyze_account_performance
        acct_num = acct_df['Account Number'].iloc[0]
        metrics = analyze_account_performance(history_df, acct_num, latest_date, acct_val)
        
        acct_invested = metrics['Total Invested']
        acct_return_dollar = metrics['Total Return ($)']
        acct_roi = metrics['ROI']
        acct_irr = metrics['IRR']
        
        print(f"{'Symbol':<10} {'Type':<6} {'Value':<12} {'Return($)':<12} {'Return(%)':<10} {'IRR':<8} {'Alloc(%)':<6}")
        for _, row in acct_df.iterrows():
            alloc = (row['Current Value'] / acct_val) * 100 if acct_val > 0 else 0
            print(f"{row['Symbol']:<10} {row['Asset Type']:<6} ${row['Current Value']:<11,.2f} ${row['Total Return ($)']:<11,.2f} {row['Total Return (%)']*100:>8.2f}% {row['IRR']*100:>7.2f}% {alloc:>7.2f}%")
            
        print(f"{'TOTAL':<10} {'-':<6} ${acct_val:<11,.2f} ${acct_return_dollar:<11,.2f} {acct_roi*100:>8.2f}% {acct_irr*100:>7.2f}% {'100.00':>7}%")


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
