#!/usr/bin/env python3
"""
Statistical Arbitrage - Cointegration Testing and Pairs Trading

This script provides tools for:
1. Cointegration testing between stock pairs
2. Pairs trading signal generation
3. Backtesting framework for statistical arbitrage strategies

Prerequisites:
    uv venv .venv
    source .venv/bin/activate
    uv pip install pandas numpy statsmodels matplotlib

Usage:
    python pairs_trading.py --help
    python pairs_trading.py test --price-a <path> --price-b <path>
    python pairs_trading.py backtest --price-a <path> --price-b <path> --entry-threshold 1.2 --exit-threshold -0.8
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.regression.linear_model import OLS
import statsmodels.api as sm


def load_price_data(file_path):
    """Load price data from CSV file."""
    df = pd.read_csv(file_path, parse_dates=['date'], index_col='date')
    return df


def calculate_correlation(price_a, price_b):
    """Calculate correlation between two price series."""
    returns_a = price_a.pct_change().dropna()
    returns_b = price_b.pct_change().dropna()
    
    # Align the series
    common_idx = returns_a.index.intersection(returns_b.index)
    return returns_a.loc[common_idx].corr(returns_b.loc[common_idx])


def cointegration_test(price_a, price_b):
    """
    Perform cointegration test between two price series.
    
    Returns:
        dict: {
            'cointegrated': bool,  # Whether the pair is cointegrated
            'p_value': float,      # P-value of the Engle-Granger test
            'test_stat': float,    # Test statistic
            'alpha': float,        # Intercept in the cointegration equation
            'beta': float,        # Slope in the cointegration equation
            'resid_std': float,   # Standard deviation of residuals
        }
    """
    # Engle-Granger两步法
    # Step 1: 回归得到残差
    X = sm.add_constant(price_b)
    model = OLS(price_a, X).fit()
    alpha = model.params.iloc[0]
    beta = model.params.iloc[1]
    residuals = model.resid
    
    # Step 2: 检验残差的平稳性 (ADF检验)
    adf_result = adfuller(residuals)
    test_stat = adf_result[0]
    p_value = adf_result[1]
    
    # 临界值（5%显著性水平）
    critical_values = adf_result[4]
    
    return {
        'cointegrated': p_value < 0.05,  # 5%显著性水平
        'p_value': p_value,
        'test_stat': test_stat,
        'alpha': alpha,
        'beta': beta,
        'resid_std': residuals.std(),
        'resid_mean': residuals.mean(),
        'critical_values': critical_values
    }


def find_cointegrated_pairs(stock_prices, threshold=0.85, min_periods=252):
    """
    Find cointegrated pairs from a list of stock prices.
    
    Args:
        stock_prices: dict of {stock_name: price_series}
        threshold: minimum correlation threshold
        min_periods: minimum periods required for testing
    
    Returns:
        list of dict: Each dict contains pair info and cointegration results
    """
    results = []
    stock_names = list(stock_prices.keys())
    
    print(f"Testing {len(stock_names) * (len(stock_names) - 1) // 2} pairs...")
    
    for i in range(len(stock_names)):
        for j in range(i + 1, len(stock_names)):
            name_a = stock_names[i]
            name_b = stock_names[j]
            
            price_a = stock_prices[name_a]
            price_b = stock_prices[name_b]
            
            # Check minimum periods
            if len(price_a) < min_periods or len(price_b) < min_periods:
                continue
            
            # Calculate correlation
            corr = calculate_correlation(price_a, price_b)
            
            if corr < threshold:
                continue
            
            # Cointegration test
            try:
                coin_result = cointegration_test(price_a, price_b)
                results.append({
                    'stock_a': name_a,
                    'stock_b': name_b,
                    'correlation': corr,
                    **coin_result
                })
            except Exception as e:
                print(f"Error testing {name_a} vs {name_b}: {e}")
                continue
    
    # Sort by p-value (most significant first)
    results.sort(key=lambda x: x['p_value'])
    
    return results


def generate_trading_signals(price_a, price_b, beta, alpha, resid_std, 
                               entry_threshold=1.2, exit_threshold=-0.8,
                               stop_loss=3.0):
    """
    Generate trading signals based on cointegration residuals.
    
    Args:
        price_a, price_b: Price series for the two stocks
        beta, alpha: Cointegration coefficients
        resid_std: Standard deviation of residuals
        entry_threshold: Entry threshold in standard deviations
        exit_threshold: Exit threshold in standard deviations
        stop_loss: Stop loss threshold in standard deviations
    
    Returns:
        DataFrame with signals and positions
    """
    # Calculate spread (residuals)
    spread = price_a - (alpha + beta * price_b)
    
    # Normalize by standard deviation
    z_score = (spread - spread.mean()) / resid_std
    
    # Generate signals
    signals = pd.DataFrame(index=price_a.index)
    signals['price_a'] = price_a
    signals['price_b'] = price_b
    signals['spread'] = spread
    signals['z_score'] = z_score
    signals['signal'] = 0  # 0: no position, 1: long spread, -1: short spread
    
    position = 0
    
    for i in range(1, len(signals)):
        z = z_score.iloc[i]
        
        if position == 0:
            # No position, check for entry
            if z > entry_threshold:
                # Spread too high: A is expensive, B is cheap -> short A, long B
                position = -1
            elif z < -entry_threshold:
                # Spread too low: A is cheap, B is expensive -> long A, short B
                position = 1
        elif position == 1:
            # Currently long spread (long A, short B)
            if z > exit_threshold or z > stop_loss:
                # Exit or stop loss
                position = 0
        elif position == -1:
            # Currently short spread (short A, long B)
            if z < -exit_threshold or z < -stop_loss:
                # Exit or stop loss
                position = 0
        
        signals.iloc[i, signals.columns.get_loc('signal')] = position
    
    return signals


def backtest_pairs_strategy(signals, transaction_cost=0.001):
    """
    Backtest pairs trading strategy.
    
    Args:
        signals: DataFrame with signals from generate_trading_signals
        transaction_cost: Transaction cost as fraction of trade value
    
    Returns:
        dict: Backtest results
    """
    # Calculate returns
    returns_a = signals['price_a'].pct_change()
    returns_b = signals['price_b'].pct_change()
    
    # Position: 1 = long spread (long A, short B)
    #          -1 = short spread (short A, long B)
    #           0 = no position
    position = signals['signal'].shift(1).fillna(0)
    
    # Spread returns (assuming equal capital allocation)
    spread_returns = position * (returns_a - returns_b)
    
    # Subtract transaction costs
    position_changes = signals['signal'].diff().abs()
    costs = position_changes * transaction_cost
    net_returns = spread_returns - costs
    
    # Cumulative returns
    cumulative_returns = (1 + net_returns).cumprod() - 1
    
    # Performance metrics
    total_return = cumulative_returns.iloc[-1]
    annual_return = (1 + total_return) ** (252 / len(signals)) - 1
    volatility = net_returns.std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility > 0 else 0
    
    # Trade statistics
    num_trades = position_changes.sum() / 2  # Each round trip is 2 changes
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe,
        'num_trades': num_trades,
        'cumulative_returns': cumulative_returns,
        'net_returns': net_returns
    }


def run_full_analysis(price_a_path, price_b_path, entry_threshold=1.2, 
                      exit_threshold=-0.8):
    """Run full analysis pipeline."""
    print(f"Loading data from {price_a_path} and {price_b_path}...")
    
    price_a = load_price_data(price_a_path)['close']
    price_b = load_price_data(price_b_path)['close']
    
    # Align data
    common_idx = price_a.index.intersection(price_b.index)
    price_a = price_a.loc[common_idx]
    price_b = price_b.loc[common_idx]
    
    print(f"Loaded {len(price_a)} data points")
    
    # Correlation
    corr = calculate_correlation(price_a, price_b)
    print(f"\nCorrelation: {corr:.4f}")
    
    # Cointegration test
    print("\nCointegration Test:")
    coin_result = cointegration_test(price_a, price_b)
    print(f"  Cointegrated: {coin_result['cointegrated']}")
    print(f"  P-value: {coin_result['p_value']:.4f}")
    print(f"  Alpha: {coin_result['alpha']:.4f}")
    print(f"  Beta: {coin_result['beta']:.4f}")
    print(f"  Residual Std: {coin_result['resid_std']:.4f}")
    
    # Generate signals
    print(f"\nGenerating trading signals (entry={entry_threshold}, exit={exit_threshold})...")
    signals = generate_trading_signals(
        price_a, price_b,
        coin_result['beta'], coin_result['alpha'], coin_result['resid_std'],
        entry_threshold, exit_threshold
    )
    
    # Backtest
    print("\nBacktest Results:")
    results = backtest_pairs_strategy(signals)
    print(f"  Total Return: {results['total_return']:.2%}")
    print(f"  Annual Return: {results['annual_return']:.2%}")
    print(f"  Volatility: {results['volatility']:.2%}")
    print(f"  Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"  Number of Trades: {results['num_trades']:.0f}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Statistical Arbitrage - Cointegration Testing and Pairs Trading'
    )
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test cointegration')
    test_parser.add_argument('--price-a', required=True, help='Path to price data CSV for stock A')
    test_parser.add_argument('--price-b', required=True, help='Path to price data CSV for stock B')
    
    # Backtest command
    bt_parser = subparsers.add_parser('backtest', help='Backtest pairs trading')
    bt_parser.add_argument('--price-a', required=True, help='Path to price data CSV for stock A')
    bt_parser.add_argument('--price-b', required=True, help='Path to price data CSV for stock B')
    bt_parser.add_argument('--entry-threshold', type=float, default=1.2, 
                           help='Entry threshold in standard deviations')
    bt_parser.add_argument('--exit-threshold', type=float, default=-0.8,
                           help='Exit threshold in standard deviations')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        run_full_analysis(args.price_a, args.price_b)
    elif args.command == 'backtest':
        run_full_analysis(args.price_a, args.price_b, args.entry_threshold, args.exit_threshold)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
