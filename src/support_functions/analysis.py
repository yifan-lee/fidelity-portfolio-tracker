import pandas as pd


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

            


        











        
# Example usage block (not executed on import)
if __name__ == "__main__":
    pass
