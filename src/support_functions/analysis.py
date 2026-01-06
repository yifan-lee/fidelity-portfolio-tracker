import pandas as pd
from pathlib import Path

from support_functions.data_loader import load_data
from support_functions.flow_builders import (
    build_stock_cash_flows, build_account_cash_flows, EntityCashFlows
)
from support_functions.math_utils import calculate_metrics


def analyze_total_performance(data):
    latest_date = data.latest_date
    unique_accounts = data.unique_accounts
    total_cash_flows = EntityCashFlows(latest_date=latest_date)

    for _, row in unique_accounts.iterrows():
        account_num = row['Account Number']
        entity_cash_flows = build_account_cash_flows(data, account_num)
        total_cash_flows.cash_flows.extend(entity_cash_flows.cash_flows)
        total_cash_flows.total_invested += entity_cash_flows.total_invested
        total_cash_flows.current_value += entity_cash_flows.current_value

    metrics = calculate_metrics(total_cash_flows)
    current_value = total_cash_flows.current_value   
    total_invested = total_cash_flows.total_invested 
    total_return = metrics['Total Return ($)']
    total_return_ratio = metrics['ROI']
    irr = metrics['IRR']
    holding_period = metrics['Holding Period (Y)']
    result = [{
        'Account Name': None,
        'Account Number': None,
        'Symbol': None,
        'Asset Type': 'All',
        'Current Value': current_value,
        'Total Invested': total_invested,
        'Total Return ($)': total_return,
        'Total Return (%)': f"{total_return_ratio:.2%}",
        'IRR': f"{irr:.2%}" if irr is not None else "N/A",
        'Investment Ratio': "100%",
        'Holding Period (Y)': f"{holding_period:.2f}"
    }]
    return pd.DataFrame(result)
    

def analyze_account_performance(data):
    unique_accounts = data.unique_accounts
    results = []
    
    for _, row in unique_accounts.iterrows():
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

def analyze_stock_performance(data):
    results = []

    positions = data.positions
    unique_accounts = data.unique_accounts

    for _, row in unique_accounts.iterrows():
        
        account_name = row['Account Name']
        account_num = row['Account Number']

        if account_name in ['ERNST & YOUNG 401(K)', 'Cash Management (Individual)','Health Savings Account']:
            continue
        
        target_type = 'Stock'
        sub_positions = positions[
            (positions['Account Name'] == account_name) &
            (positions['Asset Type'] == target_type)
        ]

        for _, sub_row in sub_positions.iterrows():
            symbol = sub_row['Symbol']
            if symbol in ['Pending activity']:
                continue
        
            entity_cash_flows = build_stock_cash_flows(data, account_num=account_num, symbol=symbol)
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
                'Symbol': symbol,
                'Asset Type': 'Stock',
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

if __name__ == "__main__":
    from support_functions.data_loader import load_data
    from support_functions.flow_builders import build_stock_cash_flows, build_account_cash_flows
    from support_functions.math_utils import calculate_metrics
    
    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    
    data = load_data(data_dir)
    result = analyze_account_performance(data)
    print(result)

    result = analyze_stock_performance(data)
    print(result)

    result = analyze_total_performance(data)
    print(result)
