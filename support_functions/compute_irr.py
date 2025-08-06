from scipy.optimize import newton
import numpy as np
def compute_irr(cashflows, dates, cob):
    """用 Newton-Raphson 方法计算 IRR（连续复利）"""
    def npv(r):
        return sum(cf * np.exp(-r * (cob - d).days / 365.0) for cf, d in zip(cashflows, dates))
    try:
        result = -newton(npv, 0.1)
    except RuntimeError:
        result = np.nan
    return result