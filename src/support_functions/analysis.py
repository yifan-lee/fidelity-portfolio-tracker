import pandas as pd
from pathlib import Path

from support_functions.data_loader import load_data
from support_functions.flow_builders import build_stock_cash_flows, build_account_cash_flows
from support_functions.math_utils import calculate_metrics


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
    

def analyze_account_performance(data):
    positions = data.positions
    results = []
    
    accounts_unique = positions.groupby(['Account Number','Account Name'])['Current Value'].sum().reset_index()
    
    for _, row in accounts_unique.iterrows():
        account_name = row['Account Name']
        account_num = row['Account Number']
        entity_cash_flows = build_account_cash_flows(data, account_num)
        metrics = calculate_metrics(entity_cash_flows)

        current_value = entity_cash_flows.current_value   
        total_invested = entity_cash_flows.total_invested 
        total_return = metrics['Total Return ($)']
        total_return_ratio = metrics['ROI']
        irr = metrics['IRR']
        holding_period = metrics['Holding Period (Y)']
        
        
        
        results.append({
            'Account Name': account_name,
            'Account Number': account_num,
            'Symbol': None,
            'Asset Type': 'Account',
            'Current Value': current_value,
            'Total Invested': total_invested,
            'Total Return ($)': total_return,
            'Total Return (%)': f"{total_return_ratio:.2%}",
            'IRR': f"{irr:.2%}" if irr is not None else "N/A",
            'Holding Period (Y)': f"{holding_period:.2f}"
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

if __name__ == "__main__":
    from support_functions.data_loader import load_data
    from support_functions.flow_builders import build_stock_cash_flows, build_account_cash_flows
    from support_functions.math_utils import calculate_metrics
    
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    
    data = load_data(data_dir)
    result = analyze_account_performance(data)
    print(result)
