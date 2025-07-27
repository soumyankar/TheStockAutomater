#!/usr/bin/env python3
"""
Trading 212 Portfolio Analyzer
=============================
Analyzes Trading 212 CSV statements and generates a comprehensive portfolio summary.

Features:
- Handles mixed datetime formats (with/without milliseconds)
- Multi-currency support with real-time FX conversion
- Calculates all key portfolio metrics
- Generates prettified text report

Usage:
    python portfolio_analyzer.py

Requirements:
    pip install pandas yfinance
"""

import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import warnings
import os
warnings.filterwarnings('ignore')

def parse_mixed_datetime(time_str):
    """Parse datetime strings with mixed formats (with and without milliseconds)"""
    if pd.isna(time_str):
        return pd.NaT

    try:
        # Try parsing with milliseconds first
        if '.' in str(time_str):
            return pd.to_datetime(time_str, format='%Y-%m-%d %H:%M:%S.%f')
        else:
            return pd.to_datetime(time_str, format='%Y-%m-%d %H:%M:%S')
    except:
        # Fallback to automatic parsing
        return pd.to_datetime(time_str, errors='coerce')

def get_fx_rate(from_currency, to_currency='EUR'):
    """Get current FX rate from yfinance"""
    if from_currency == to_currency:
        return 1.0

    try:
        if from_currency == 'USD':
            ticker = 'EURUSD=X'
            rate = yf.Ticker(ticker).info.get('regularMarketPrice', 1.08)
            return 1/rate  # Convert USD to EUR
        elif from_currency == 'GBP':
            ticker = 'EURGBP=X'
            rate = yf.Ticker(ticker).info.get('regularMarketPrice', 0.85)
            return 1/rate  # Convert GBP to EUR
        else:
            return 1.0
    except:
        # Fallback rates
        fallback_rates = {'USD': 0.92, 'GBP': 1.17}
        return fallback_rates.get(from_currency, 1.0)

def get_correct_ticker_and_price(ticker):
    """Get the correct ticker symbol and current price"""
    ticker_mappings = {
        'VUSA': 'VUSA.L',  # UK-listed ETF needs .L suffix
        'AAPL': 'AAPL',
        'AMZN': 'AMZN',
        'AMD': 'AMD',
        'MSFT': 'MSFT',
        'NVDA': 'NVDA'
    }

    yf_ticker = ticker_mappings.get(ticker, ticker)

    try:
        stock = yf.Ticker(yf_ticker)

        # Try to get recent data
        hist = stock.history(period='5d')
        if not hist.empty:
            price = hist['Close'].iloc[-1]
            info = stock.info
            currency = info.get('currency', 'USD')
            return price, currency
        else:
            # Try info as fallback
            info = stock.info
            price = info.get('regularMarketPrice', info.get('currentPrice', 0))
            currency = info.get('currency', 'USD')
            return price, currency

    except Exception as e:
        print(f"    ⚠️  Error fetching {ticker} ({yf_ticker}): {e}")
        return 0, 'EUR'

def analyze_portfolio():
    """Main portfolio analysis function"""
    print("📁 Files in the current directory:")
    current_dir = os.path.dirname(__file__)
    for filename in os.listdir(current_dir):
        print("  •", filename)
    
    csv_file = os.path.join(os.path.dirname(__file__), "combined_statement.csv")

    print("🔄 Loading and processing Trading 212 statement...")

    # Load CSV with robust parsing
    try:
        df = pd.read_csv(csv_file, quotechar='"', on_bad_lines='skip')
    except FileNotFoundError:
        print(f"❌ Error: Could not find {csv_file}")
        print("Please ensure your CSV file is named 'combined_statement.csv' and is in the same directory.")
        return
    except Exception as e:
        print(f"❌ Error loading CSV file: {e}")
        return

    # Parse datetime with mixed formats
    df['DateTime'] = df['Time'].apply(parse_mixed_datetime)
    df = df.sort_values('DateTime').reset_index(drop=True)

    print(f"✅ Loaded {len(df)} transactions")
    print(f"📅 Date range: {df['DateTime'].min()} to {df['DateTime'].max()}")

    for csv_line, row in df.iterrows():
        print(f"→ CSV line {csv_line + 2}: "
          f"{row['Time']} | {row['Action']} | {row.get('Ticker', '')}")

    # Initialize portfolio tracking
    cash = 0.0
    positions = {}  # ticker -> {'shares': float, 'cost_eur': float, 'transactions': []}

    print("\n🔄 Processing transactions...")

    for idx, row in df.iterrows():
        action = row['Action']
        amount = pd.to_numeric(row['Total'], errors='coerce') or 0

        if action == 'Deposit':
            cash += amount

        elif action == 'Withdrawal':
            cash += amount  # Amount is already negative for withdrawals

        elif action == 'Interest on cash':
            cash += amount

        elif action in ['Market buy', 'Limit buy']:
            ticker = row['Ticker']
            shares = pd.to_numeric(row['Quantity'], errors='coerce') or 0
            cost_eur = abs(amount)  # Total is negative for buys
            conv_fee = pd.to_numeric(row['Currency conversion fee'], errors='coerce') or 0
            total_cost = cost_eur + conv_fee

            cash -= total_cost

            if ticker not in positions:
                positions[ticker] = {'shares': 0, 'cost_eur': 0, 'transactions': []}

            positions[ticker]['shares'] += shares
            positions[ticker]['cost_eur'] += total_cost
            positions[ticker]['transactions'].append({
                'date': row['DateTime'],
                'action': 'buy',
                'shares': shares,
                'cost': total_cost
            })

        elif action in ['Market sell', 'Limit sell']:
            ticker = row['Ticker']
            shares = pd.to_numeric(row['Quantity'], errors='coerce') or 0
            proceeds_eur = abs(amount)
            conv_fee = pd.to_numeric(row['Currency conversion fee'], errors='coerce') or 0
            net_proceeds = proceeds_eur - conv_fee

            cash += net_proceeds

            if ticker in positions:
                # Reduce shares
                positions[ticker]['shares'] -= shares

                # Reduce cost basis proportionally
                if positions[ticker]['shares'] > 0:
                    cost_reduction_ratio = shares / (positions[ticker]['shares'] + shares)
                    positions[ticker]['cost_eur'] *= (1 - cost_reduction_ratio)
                else:
                    positions[ticker]['cost_eur'] = 0

                positions[ticker]['transactions'].append({
                    'date': row['DateTime'],
                    'action': 'sell',
                    'shares': shares,
                    'proceeds': net_proceeds
                })

    # Remove positions with zero or negative shares
    positions = {k: v for k, v in positions.items() if v['shares'] > 0.001}

    print(f"💰 Final cash position: €{cash:.2f}")
    print(f"📊 Active positions: {len(positions)}")

    if not positions:
        print("❌ No active positions found")
        return

    print(f"🎯 Tickers: {', '.join(positions.keys())}")

    # Get current prices and calculate portfolio metrics
    print("\n🔄 Fetching current market prices...")

    portfolio_data = []
    total_invested = 0
    total_market_value = 0

    for ticker, position in positions.items():
        shares = position['shares']
        cost_eur = position['cost_eur']
        avg_cost = cost_eur / shares if shares > 0 else 0

        print(f"📈 Getting price for {ticker}...")
        current_price_native, currency = get_correct_ticker_and_price(ticker)

        # Convert to EUR if needed
        if currency != 'EUR':
            fx_rate = get_fx_rate(currency, 'EUR')
            current_price_eur = current_price_native * fx_rate
        else:
            current_price_eur = current_price_native

        market_value = current_price_eur * shares
        pnl_eur = market_value - cost_eur
        pnl_percent = (pnl_eur / cost_eur * 100) if cost_eur > 0 else 0

        portfolio_data.append({
            'Ticker': ticker,
            'Shares': shares,
            'Avg Euro': avg_cost,
            'Cost Euro': cost_eur,
            'Price Euro': current_price_eur,
            'Value Euro': market_value,
            'P&L Euro': pnl_eur,
            'P&L %': pnl_percent
        })

        total_invested += cost_eur
        total_market_value += market_value

    # Calculate totals
    total_account_value = cash + total_market_value
    unrealized_pnl = total_market_value - total_invested
    unrealized_pnl_percent = (unrealized_pnl / total_invested * 100) if total_invested > 0 else 0

    # Sort by value (largest positions first)
    sorted_portfolio = sorted(portfolio_data, key=lambda x: x['Value Euro'], reverse=True)

    # Generate report
    print("\n" + "="*80)
    print("🏦 TRADING 212 PORTFOLIO SUMMARY")
    print("="*80)

    # Account Summary
    print("\n📊 ACCOUNT SUMMARY")
    print("-" * 40)
    print(f"Free cash        : €{cash:>12,.2f}")
    print(f"Invested amount  : €{total_invested:>12,.2f}")
    print(f"Portfolio value  : €{total_market_value:>12,.2f}")
    print("-" * 40)
    print(f"TOTAL ACCOUNT    : €{total_account_value:>12,.2f}")
    print(f"Unrealised P&L   : €{unrealized_pnl:>12,.2f}  ({unrealized_pnl_percent:>6.2f}%)")

    # Ticker Summary Table
    print(f"\n📈 TICKER SUMMARY")
    print("-" * 80)
    print(f"{'Ticker':<8} {'Shares':<9} {'Avg €':<8} {'Cost €':<10} {'Price €':<9} {'Value €':<11} {'P&L €':<10} {'P&L %':<8}")
    print("-" * 80)

    for position in sorted_portfolio:
        print(f"{position['Ticker']:<8} "
              f"{position['Shares']:>8.3f} "
              f"{position['Avg Euro']:>8.2f} "
              f"{position['Cost Euro']:>10.2f} "
              f"{position['Price Euro']:>9.2f} "
              f"{position['Value Euro']:>11.2f} "
              f"{position['P&L Euro']:>10.2f} "
              f"{position['P&L %']:>7.2f}%")

    print("-" * 80)
    print(f"{'TOTAL':<8} {'':<9} {'':<8} {total_invested:>10.2f} {'':<9} {total_market_value:>11.2f} {unrealized_pnl:>10.2f} {unrealized_pnl_percent:>7.2f}%")

    # Additional metrics
    print(f"\n📋 ADDITIONAL METRICS")
    print("-" * 40)
    largest_position = max(sorted_portfolio, key=lambda x: x['Value Euro'])
    best_performer = max(sorted_portfolio, key=lambda x: x['P&L %'])
    worst_performer = min(sorted_portfolio, key=lambda x: x['P&L %'])

    print(f"Largest position  : {largest_position['Ticker']} (€{largest_position['Value Euro']:,.2f})")
    print(f"Best performer    : {best_performer['Ticker']} ({best_performer['P&L %']:+.2f}%)")
    print(f"Worst performer   : {worst_performer['Ticker']} ({worst_performer['P&L %']:+.2f}%)")
    print(f"Portfolio size    : {len(positions)} positions")
    print(f"Cash allocation   : {(cash/total_account_value)*100:.1f}% of total account")

    print(f"\n🕐 Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # Create the report content for file
    report_content = f"""================================================================================
🏦 TRADING 212 PORTFOLIO SUMMARY
================================================================================

📊 ACCOUNT SUMMARY
----------------------------------------
Free cash        : €{cash:>12,.2f}
Invested amount  : €{total_invested:>12,.2f}
Portfolio value  : €{total_market_value:>12,.2f}
----------------------------------------
TOTAL ACCOUNT    : €{total_account_value:>12,.2f}
Unrealised P&L   : €{unrealized_pnl:>12,.2f}  ({unrealized_pnl_percent:>6.2f}%)

📈 TICKER SUMMARY
--------------------------------------------------------------------------------
{'Ticker':<8} {'Shares':<9} {'Avg €':<8} {'Cost €':<10} {'Price €':<9} {'Value €':<11} {'P&L €':<10} {'P&L %':<8}
--------------------------------------------------------------------------------
"""

    # Add each position
    for position in sorted_portfolio:
        report_content += f"""{position['Ticker']:<8} {position['Shares']:>8.3f} {position['Avg Euro']:>8.2f} {position['Cost Euro']:>10.2f} {position['Price Euro']:>9.2f} {position['Value Euro']:>11.2f} {position['P&L Euro']:>10.2f} {position['P&L %']:>7.2f}%
"""

    report_content += f"""--------------------------------------------------------------------------------
{'TOTAL':<8} {'':<9} {'':<8} {total_invested:>10.2f} {'':<9} {total_market_value:>11.2f} {unrealized_pnl:>10.2f} {unrealized_pnl_percent:>7.2f}%

📋 ADDITIONAL METRICS
----------------------------------------
Largest position  : {largest_position['Ticker']} (€{largest_position['Value Euro']:,.2f})
Best performer    : {best_performer['Ticker']} ({best_performer['P&L %']:+.2f}%)
Worst performer   : {worst_performer['Ticker']} ({worst_performer['P&L %']:+.2f}%)
Portfolio size    : {len(positions)} positions
Cash allocation   : {(cash/total_account_value)*100:.1f}% of total account

🕐 Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data source: Trading 212 combined statement
================================================================================
"""

    # Create exports directory if it doesn't exist
    if not os.path.exists('exports'):
        os.makedirs('exports')

    # Save the report
    with open('exports/portfolio_summary.txt', 'w', encoding='utf-8') as f:
        f.write(report_content)

    print("\n💾 Portfolio summary saved to: exports/portfolio_summary.txt")
    print("\n✅ Analysis complete! Your portfolio shows:")
    print(f"   • Total account value: €{total_account_value:,.2f}")
    print(f"   • Unrealized P&L: €{unrealized_pnl:,.2f} ({unrealized_pnl_percent:+.2f}%)")
    print(f"   • {len(positions)} active positions")

if __name__ == "__main__":
    print("🚀 Trading 212 Portfolio Analyzer")
    print("=" * 50)

    try:
        analyze_portfolio()
    except KeyboardInterrupt:
        print("\n\n👋 Analysis interrupted by user.")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        print("Please check your CSV file and try again.")
