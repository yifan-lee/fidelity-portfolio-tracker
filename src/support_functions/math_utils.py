import numpy as np
import pandas as pd
from pathlib import Path
from scipy import optimize



## Math Core Layer

def calculate_metrics(entity_cash_flows):
    cash_flows = entity_cash_flows.cash_flows
    total_invested = entity_cash_flows.total_invested
    current_value = entity_cash_flows.current_value
    latest_date = entity_cash_flows.latest_date

    irr_val = xirr(cash_flows)
    total_return_dollar = current_value - total_invested
    roi = total_return_dollar / total_invested if total_invested != 0 else 0
    weighted_average_holding_period = get_weighted_average_holding_period(cash_flows, latest_date)
    
    return {
        'IRR': irr_val,
        'Total Return ($)': total_return_dollar,
        'ROI': roi,
        'Holding Period (Y)': weighted_average_holding_period
    }

def get_weighted_average_holding_period(cash_flows, latest_date):
    invested_cash_flows = [flow for flow in cash_flows if flow[1] < 0]
    dates, amounts = zip(*invested_cash_flows)
    amounts = pd.Series(amounts)
    amounts_ratio = amounts/amounts.sum()
    holding_period = pd.Series([(latest_date - d).days for d in dates])
    return (amounts_ratio*holding_period).sum()/365.0
    


def xirr(cash_flows):
    """
    Calculate Internal Rate of Return (XIRR).
    cash_flows: List of (date, amount) tuples.
    """
    if not cash_flows or len(cash_flows) < 2:
        return None
        
    dates, amounts = zip(*cash_flows)
    
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

if __name__ == "__main__":
    from support_functions.data_loader import load_data
    from support_functions.flow_builders import build_stock_cash_flows, build_account_cash_flows

    project_path= Path.cwd()
    data_dir = f'{project_path}/data'
    output_dir = f'{project_path}/output'

    data = load_data(data_dir)

    account = 'Z23390746'
    symbol = 'AAPL'
    entity_cash_flows = build_stock_cash_flows(data, account, symbol)
    metrics = calculate_metrics(entity_cash_flows)
    print(metrics)

    account = 'Z23390746'
    entity_cash_flows = build_account_cash_flows(data, account)
    metrics = calculate_metrics(entity_cash_flows)
    print(metrics)