# --- AI Analytics & Predictive Insights ---
def ai_analytics_section():
    st.header("AI Analytics & Predictive Insights")
    # SACCO forecast
    sacco_df = fetch_table('sacco')
    if not sacco_df.empty and len(sacco_df) > 2:
        sacco_df = sacco_df.sort_values(['year', 'month'])
        sacco_df['month_num'] = sacco_df['month'].apply(lambda m: datetime.strptime(m, "%B").month)
        sacco_df['date'] = pd.to_datetime(sacco_df['year'].astype(str) + '-' + sacco_df['month_num'].astype(str) + '-01')
        sacco_df = sacco_df.sort_values('date')
        sacco_df['cum_contrib'] = sacco_df['contribution'].cumsum()
        X = (sacco_df['date'] - sacco_df['date'].min()).dt.days.values.reshape(-1, 1)
        y = sacco_df['cum_contrib'].values
        model = LinearRegression().fit(X, y)
        future_days = (pd.to_datetime(f"{datetime.now().year}-12-01") - sacco_df['date'].min()).days
        forecast = model.predict([[future_days]])[0]
        st.info(f"AI Forecast: Estimated total SACCO contributions by Dec {datetime.now().year}: {forecast:,.0f} KES")
    # Stocks forecast
    stocks_df = fetch_table('stocks')
    if not stocks_df.empty and len(stocks_df) > 2:
        stocks_df = stocks_df.sort_values('ticker')
        X = stocks_df['shares'].values.reshape(-1, 1)
        y = stocks_df['current_price'].values
        model = LinearRegression().fit(X, y)
        next_shares = X.max() + 10
        price_pred = model.predict([[next_shares]])[0]
        st.info(f"AI Forecast: If you increase your largest stock holding by 10 shares, expected price: {price_pred:,.2f} KES")

# --- Stocks Section ---
def stocks_section():
    st.header("NSE & Global Stocks")
    stocks_df = fetch_table('stocks')
    st.write("### Stock Holdings", stocks_df)
    # Add new stock form
    with st.form("stocks_form", clear_on_submit=True):
        st.write("#### Add Stock")
        ticker = st.text_input("Ticker (e.g. KGN.NR, AAPL)", value="KGN.NR")
        shares = st.number_input("Shares", min_value=0.0, value=0.0, step=1.0)
        purchase_price = st.number_input("Purchase Price (KES)", min_value=0.0, value=0.0, step=1.0)
        current_price = st.number_input("Current Price (KES)", min_value=0.0, value=0.0, step=1.0)
        submitted = st.form_submit_button("Add Stock")
        if submitted and shares > 0:
            conn = get_connection()
            conn.execute("INSERT INTO stocks (ticker, shares, purchase_price, current_price) VALUES (?, ?, ?, ?)", (ticker.upper(), shares, purchase_price, current_price))
            conn.commit()
            conn.close()
            st.success(f"Added {shares} shares of {ticker.upper()} at {purchase_price} KES")
            st.experimental_rerun()
    # Show table with PnL
    if not stocks_df.empty:
        stocks_df['market_value'] = stocks_df['shares'] * stocks_df['current_price']
        stocks_df['pnl'] = (stocks_df['current_price'] - stocks_df['purchase_price']) * stocks_df['shares']
        stocks_df['pnl_pct'] = 100 * (stocks_df['current_price'] - stocks_df['purchase_price']) / stocks_df['purchase_price'].replace(0, 1)
        st.write("### Stock Table", stocks_df[['ticker', 'shares', 'purchase_price', 'current_price', 'market_value', 'pnl', 'pnl_pct']])
        st.metric("Stocks Portfolio Value (KES)", f"{stocks_df['market_value'].sum():,.2f}")
    else:
        st.info("No stock holdings yet.")

# --- Money Market Fund Section ---
def mmf_section():
    st.header("Money Market Fund (MMF)")
    mmf_df = fetch_table('mmf')
    st.write("### MMF Holdings", mmf_df)
    # Add/update MMF form
    with st.form("mmf_form", clear_on_submit=True):
        st.write("#### Update MMF Balance")
        name = st.text_input("Fund Name", value="Etica Money Market Fund")
        balance = st.number_input("Balance (KES)", min_value=0.0, value=0.0, step=100.0)
        annual_rate = st.number_input("Annual Rate (%)", min_value=0.0, value=9.0, step=0.01)
        last_update = st.date_input("Last Update", value=datetime.now())
        submitted = st.form_submit_button("Update MMF")
        if submitted:
            conn = get_connection()
            # Only one MMF row for simplicity
            conn.execute("DELETE FROM mmf")
            conn.execute("INSERT INTO mmf (name, balance, annual_rate, last_update) VALUES (?, ?, ?, ?)", (name, balance, annual_rate, last_update.strftime('%Y-%m-%d')))
            conn.commit()
            conn.close()
            st.success(f"MMF updated: {balance} KES at {annual_rate}% annual rate")
            st.experimental_rerun()
    # Calculate value using daily rate
    if not mmf_df.empty:
        row = mmf_df.iloc[0]
        principal = row['balance']
        annual_rate = row['annual_rate']
        last_update = pd.to_datetime(row['last_update'])
        days = (datetime.now() - last_update).days
        daily_rate = annual_rate / 100 / 365
        value = principal * ((1 + daily_rate) ** days)
        st.metric("MMF Value (KES)", f"{value:,.2f}")
        st.caption(f"Estimated using {annual_rate}% annual rate, {days} days since last update.")
    else:
        st.info("No MMF balance yet.")

# --- Crypto Portfolio Section ---
def fetch_crypto_prices(symbols):
    ids_map = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'SOL': 'solana', 'BNB': 'binancecoin', 'XRP': 'ripple'
    }
    ids = ','.join([ids_map.get(sym.upper(), sym.lower()) for sym in symbols])
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd'
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        return {k.upper(): v['usd'] for k, v in data.items()}
    except Exception:
        return {sym: 0 for sym in symbols}

def crypto_section():
    st.header("Cryptocurrency Portfolio")
    crypto_df = fetch_table('crypto')
    st.write("### Holdings", crypto_df)
    # Add new crypto form
    with st.form("crypto_form", clear_on_submit=True):
        st.write("#### Add Cryptocurrency")
        symbol = st.text_input("Symbol (e.g. BTC)", value="BTC")
        amount = st.number_input("Amount Held", min_value=0.0, value=0.0, step=0.01)
        purchase_price = st.number_input("Purchase Price (USD)", min_value=0.0, value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Crypto")
        if submitted and amount > 0:
            conn = get_connection()
            conn.execute("INSERT INTO crypto (symbol, amount, purchase_price) VALUES (?, ?, ?)", (symbol.upper(), amount, purchase_price))
            conn.commit()
            conn.close()
            st.success(f"Added {amount} {symbol.upper()} at ${purchase_price}")
            st.experimental_rerun()
    # Fetch real-time prices
    if not crypto_df.empty:
        symbols = crypto_df['symbol'].unique().tolist()
        prices = fetch_crypto_prices(symbols)
        crypto_df['current_price'] = crypto_df['symbol'].apply(lambda s: prices.get(s.upper(), 0))
        crypto_df['market_value'] = crypto_df['amount'] * crypto_df['current_price']
        st.write("### Real-Time Prices & Value", crypto_df[['symbol', 'amount', 'purchase_price', 'current_price', 'market_value']])
        st.metric("Crypto Portfolio Value (USD)", f"{crypto_df['market_value'].sum():,.2f}")
    else:
        st.info("No crypto holdings yet.")

# --- Government Bonds Section ---
def bonds_section():
    st.header("Government Bonds")
    bonds_df = fetch_table('bonds')
    st.write("### Bond Holdings", bonds_df)
    # Add new bond form
    with st.form("bonds_form", clear_on_submit=True):
        st.write("#### Add New Bond")
        name = st.text_input("Bond Name", value="Sample Bond")
        principal = st.number_input("Principal (KES)", min_value=0.0, value=0.0, step=1000.0)
        rate = st.number_input("Interest Rate (%)", min_value=0.0, value=12.8, step=0.01)
        start_date = st.date_input("Start Date", value=datetime.now())
        duration_months = st.number_input("Duration (months)", min_value=1, value=12, step=1)
        submitted = st.form_submit_button("Add Bond")
        if submitted and principal > 0:
            conn = get_connection()
            conn.execute("INSERT INTO bonds (name, principal, rate, start_date, duration_months) VALUES (?, ?, ?, ?, ?)", (name, principal, rate, start_date.strftime('%Y-%m-%d'), duration_months))
            conn.commit()
            conn.close()
            st.success(f"Added bond {name} with {principal} KES at {rate}%")
            st.experimental_rerun()
    # Calculate total interest
    if not bonds_df.empty:
        bonds_df['interest'] = bonds_df['principal'] * (bonds_df['rate'] / 100) * (bonds_df['duration_months'] / 12)
        st.write("### Interest Summary", bonds_df[['name', 'principal', 'rate', 'duration_months', 'interest']])
        st.metric("Total Bond Interest (KES)", f"{bonds_df['interest'].sum():,.2f}")
    else:
        st.info("No bonds added yet.")

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import requests
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

DB_NAME = 'portfolio.db'

# Utility functions for DB

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def fetch_table(table):
    conn = get_connection()
    df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
    conn.close()
    return df

# --- Streamlit App ---
st.set_page_config(page_title="Kenya Multi-Asset Portfolio Tracker", layout="wide")
st.title("🇰🇪 Multi-Asset Portfolio Tracker & Analytics Dashboard")

# --- Sidebar: Asset Toggles ---
st.sidebar.header("Toggle Asset Classes")
asset_types = ["SACCO", "Bonds", "Crypto", "MMF", "Stocks"]
conn = get_connection()
conn.execute('CREATE TABLE IF NOT EXISTS toggles (asset_type TEXT PRIMARY KEY, enabled INTEGER DEFAULT 1)')
conn.commit()
toggle_states = {}
for asset in asset_types:
    cur = conn.execute('SELECT enabled FROM toggles WHERE asset_type = ?', (asset,))
    row = cur.fetchone()
    default = True if row is None else bool(row[0])
    toggle = st.sidebar.checkbox(asset, value=default)
    toggle_states[asset] = toggle
    conn.execute('INSERT OR REPLACE INTO toggles (asset_type, enabled) VALUES (?, ?)', (asset, int(toggle)))
conn.commit()
conn.close()
toggles = toggle_states


# --- Main Dashboard Layout ---
st.subheader("Portfolio Overview")

# Aggregate portfolio values
def get_portfolio_summary():
    sacco_df = fetch_table('sacco') if toggles.get('SACCO', True) else pd.DataFrame()
    bonds_df = fetch_table('bonds') if toggles.get('Bonds', True) else pd.DataFrame()
    crypto_df = fetch_table('crypto') if toggles.get('Crypto', True) else pd.DataFrame()
    mmf_df = fetch_table('mmf') if toggles.get('MMF', True) else pd.DataFrame()
    stocks_df = fetch_table('stocks') if toggles.get('Stocks', True) else pd.DataFrame()
    # SACCO
    sacco_val = 0
    if not sacco_df.empty:
        months = len(sacco_df)
        total_contrib = sacco_df['contribution'].sum()
        interest_rate = sacco_df['interest_rate'].iloc[0] if 'interest_rate' in sacco_df else 0.13
        sacco_val = total_contrib * (1 + interest_rate * months / 12)
    # Bonds
    bonds_val = 0
    if not bonds_df.empty:
        bonds_df['interest'] = bonds_df['principal'] * (bonds_df['rate'] / 100) * (bonds_df['duration_months'] / 12)
        bonds_val = bonds_df['principal'].sum() + bonds_df['interest'].sum()
    # Crypto (USD to KES, assume 1 USD = 150 KES for now)
    crypto_val = 0
    if not crypto_df.empty:
        symbols = crypto_df['symbol'].unique().tolist()
        prices = {s: 0 for s in symbols}
        try:
            prices = fetch_crypto_prices(symbols)
        except Exception:
            pass
        crypto_df['current_price'] = crypto_df['symbol'].apply(lambda s: prices.get(s.upper(), 0))
        crypto_df['market_value'] = crypto_df['amount'] * crypto_df['current_price']
        crypto_val = crypto_df['market_value'].sum() * 150
    # MMF
    mmf_val = 0
    if not mmf_df.empty:
        row = mmf_df.iloc[0]
        principal = row['balance']
        annual_rate = row['annual_rate']
        last_update = pd.to_datetime(row['last_update'])
        days = (datetime.now() - last_update).days
        daily_rate = annual_rate / 100 / 365
        mmf_val = principal * ((1 + daily_rate) ** days)
    # Stocks
    stocks_val = 0
    stocks_pnl = 0
    if not stocks_df.empty:
        stocks_df['market_value'] = stocks_df['shares'] * stocks_df['current_price']
        stocks_df['pnl'] = (stocks_df['current_price'] - stocks_df['purchase_price']) * stocks_df['shares']
        stocks_val = stocks_df['market_value'].sum()
        stocks_pnl = stocks_df['pnl'].sum()
    # PnL (simplified)
    total_val = sacco_val + bonds_val + crypto_val + mmf_val + stocks_val
    total_pnl = bonds_val + crypto_val + mmf_val + stocks_val + sacco_val - (
        sacco_df['contribution'].sum() if not sacco_df.empty else 0
        + bonds_df['principal'].sum() if not bonds_df.empty else 0
        + crypto_df['amount'].sum() * 0 if not crypto_df.empty else 0
        + (mmf_df['balance'].sum() if not mmf_df.empty else 0)
        + stocks_df['purchase_price'].sum() if not stocks_df.empty else 0
    )
    asset_vals = {
        'SACCO': sacco_val,
        'Bonds': bonds_val,
        'Crypto': crypto_val,
        'MMF': mmf_val,
        'Stocks': stocks_val
    }
    best_asset = max(asset_vals, key=asset_vals.get) if total_val > 0 else '-'
    worst_asset = min(asset_vals, key=asset_vals.get) if total_val > 0 else '-'
    return total_val, total_pnl, best_asset, worst_asset, asset_vals

total_val, total_pnl, best_asset, worst_asset, asset_vals = get_portfolio_summary()
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Portfolio Value (KES)", f"{total_val:,.2f}")
col2.metric("Total Profit/Loss", f"{total_pnl:,.2f}")
col3.metric("Best Performing Asset", best_asset)
col4.metric("Worst Performing Asset", worst_asset)

# Asset allocation pie chart
pie_df = pd.DataFrame({"Asset": list(asset_vals.keys()), "Value": list(asset_vals.values())})
pie_df = pie_df[pie_df['Value'] > 0]
if not pie_df.empty:
    st.plotly_chart(px.pie(pie_df, names="Asset", values="Value", title="Asset Allocation"), use_container_width=True)
else:
    st.info("No assets in portfolio yet.")


# --- Monthly PnL Tracking Table ---
st.subheader("Monthly Profit / Loss Tracking")

def get_monthly_pnl():
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    data = {"Month": months}
    # Only include enabled asset classes
    if toggles.get('SACCO', True):
        sacco_df = fetch_table('sacco')
        sacco_pnl = [sacco_df[sacco_df['month'] == m]['contribution'].sum() if not sacco_df.empty else 0 for m in months]
        data['SACCO'] = sacco_pnl
    if toggles.get('Bonds', True):
        bonds_df = fetch_table('bonds')
        bonds_pnl = [bonds_df['principal'].sum() * (bonds_df['rate'].mean()/100/12) if not bonds_df.empty else 0 for _ in months]
        data['Bonds'] = bonds_pnl
    if toggles.get('Crypto', True):
        crypto_df = fetch_table('crypto')
        crypto_val = 0
        if not crypto_df.empty:
            symbols = crypto_df['symbol'].unique().tolist()
            prices = {s: 0 for s in symbols}
            try:
                prices = fetch_crypto_prices(symbols)
            except Exception:
                pass
            crypto_df['current_price'] = crypto_df['symbol'].apply(lambda s: prices.get(s.upper(), 0))
            crypto_df['market_value'] = crypto_df['amount'] * crypto_df['current_price']
            crypto_val = crypto_df['market_value'].sum() * 150
        data['Crypto'] = [crypto_val if i == datetime.now().month-1 else 0 for i in range(12)]
    if toggles.get('MMF', True):
        mmf_df = fetch_table('mmf')
        mmf_interest = 0
        if not mmf_df.empty:
            row = mmf_df.iloc[0]
            mmf_interest = row['balance'] * (row['annual_rate']/100/12)
        data['MMF'] = [mmf_interest for _ in months]
    if toggles.get('Stocks', True):
        stocks_df = fetch_table('stocks')
        stocks_pnl = 0
        if not stocks_df.empty:
            stocks_df['pnl'] = (stocks_df['current_price'] - stocks_df['purchase_price']) * stocks_df['shares']
            stocks_pnl = stocks_df['pnl'].sum()
        data['Stocks'] = [stocks_pnl if i == datetime.now().month-1 else 0 for i in range(12)]
    return pd.DataFrame(data)

st.dataframe(get_monthly_pnl())

# --- Investment Entry Form (placeholder) ---




# --- Investment Entry/Edit Forms (Sidebar) ---
st.sidebar.header("Add / Edit Investments")

# --- Refresh Button ---
if st.sidebar.button("🔄 Refresh Portfolio Figures"):
    st.experimental_rerun()

with st.sidebar.expander("SACCO Contribution"):
    # --- Main Dashboard Layout ---
    st.subheader("Portfolio Overview")

    def get_end_of_year_totals():
        # Calculate end-of-year totals for each asset class
        sacco_df = fetch_table('sacco') if toggles.get('SACCO', True) else pd.DataFrame()
        bonds_df = fetch_table('bonds') if toggles.get('Bonds', True) else pd.DataFrame()
        crypto_df = fetch_table('crypto') if toggles.get('Crypto', True) else pd.DataFrame()
        mmf_df = fetch_table('mmf') if toggles.get('MMF', True) else pd.DataFrame()
        stocks_df = fetch_table('stocks') if toggles.get('Stocks', True) else pd.DataFrame()
        # SACCO
        sacco_val = 0
        if not sacco_df.empty:
            months = 12
            total_contrib = sacco_df['contribution'].sum()
            interest_rate = sacco_df['interest_rate'].iloc[0] if 'interest_rate' in sacco_df else 0.13
            sacco_val = total_contrib * (1 + interest_rate * months / 12)
        # Bonds
        bonds_val = 0
        if not bonds_df.empty:
            bonds_df['interest'] = bonds_df['principal'] * (bonds_df['rate'] / 100) * (bonds_df['duration_months'] / 12)
            bonds_val = bonds_df['principal'].sum() + bonds_df['interest'].sum()
        # Crypto (USD to KES, assume 1 USD = 150 KES for now)
        crypto_val = 0
        if not crypto_df.empty:
            symbols = crypto_df['symbol'].unique().tolist()
            prices = {s: 0 for s in symbols}
            try:
                prices = fetch_crypto_prices(symbols)
            except Exception:
                pass
            crypto_df['current_price'] = crypto_df['symbol'].apply(lambda s: prices.get(s.upper(), 0))
            crypto_df['market_value'] = crypto_df['amount'] * crypto_df['current_price']
            crypto_val = crypto_df['market_value'].sum() * 150
        # MMF
        mmf_val = 0
        if not mmf_df.empty:
            row = mmf_df.iloc[0]
            principal = row['balance']
            annual_rate = row['annual_rate']
            last_update = pd.to_datetime(row['last_update'])
            days = (pd.to_datetime(f"{datetime.now().year}-12-31") - last_update).days
            daily_rate = annual_rate / 100 / 365
            mmf_val = principal * ((1 + daily_rate) ** days)
        # Stocks
        stocks_val = 0
        stocks_pnl = 0
        if not stocks_df.empty:
            stocks_df['market_value'] = stocks_df['shares'] * stocks_df['current_price']
            stocks_df['pnl'] = (stocks_df['current_price'] - stocks_df['purchase_price']) * stocks_df['shares']
            stocks_val = stocks_df['market_value'].sum()
            stocks_pnl = stocks_df['pnl'].sum()
        return {
            'SACCO': sacco_val,
            'Bonds': bonds_val,
            'Crypto': crypto_val,
            'MMF': mmf_val,
            'Stocks': stocks_val
        }

    def get_portfolio_summary():
        # ...existing code for current totals...
        sacco_df = fetch_table('sacco') if toggles.get('SACCO', True) else pd.DataFrame()
        bonds_df = fetch_table('bonds') if toggles.get('Bonds', True) else pd.DataFrame()
        crypto_df = fetch_table('crypto') if toggles.get('Crypto', True) else pd.DataFrame()
        mmf_df = fetch_table('mmf') if toggles.get('MMF', True) else pd.DataFrame()
        stocks_df = fetch_table('stocks') if toggles.get('Stocks', True) else pd.DataFrame()
        # SACCO
        sacco_val = 0
        if not sacco_df.empty:
            months = len(sacco_df)
            total_contrib = sacco_df['contribution'].sum()
            interest_rate = sacco_df['interest_rate'].iloc[0] if 'interest_rate' in sacco_df else 0.13
            sacco_val = total_contrib * (1 + interest_rate * months / 12)
        # Bonds
        bonds_val = 0
        if not bonds_df.empty:
            bonds_df['interest'] = bonds_df['principal'] * (bonds_df['rate'] / 100) * (bonds_df['duration_months'] / 12)
            bonds_val = bonds_df['principal'].sum() + bonds_df['interest'].sum()
        # Crypto (USD to KES, assume 1 USD = 150 KES for now)
        crypto_val = 0
        if not crypto_df.empty:
            symbols = crypto_df['symbol'].unique().tolist()
            prices = {s: 0 for s in symbols}
            try:
                prices = fetch_crypto_prices(symbols)
            except Exception:
                pass
            crypto_df['current_price'] = crypto_df['symbol'].apply(lambda s: prices.get(s.upper(), 0))
            crypto_df['market_value'] = crypto_df['amount'] * crypto_df['current_price']
            crypto_val = crypto_df['market_value'].sum() * 150
        # MMF
        mmf_val = 0
        if not mmf_df.empty:
            row = mmf_df.iloc[0]
            principal = row['balance']
            annual_rate = row['annual_rate']
            last_update = pd.to_datetime(row['last_update'])
            days = (datetime.now() - last_update).days
            daily_rate = annual_rate / 100 / 365
            mmf_val = principal * ((1 + daily_rate) ** days)
        # Stocks
        stocks_val = 0
        stocks_pnl = 0
        if not stocks_df.empty:
            stocks_df['market_value'] = stocks_df['shares'] * stocks_df['current_price']
            stocks_df['pnl'] = (stocks_df['current_price'] - stocks_df['purchase_price']) * stocks_df['shares']
            stocks_val = stocks_df['market_value'].sum()
            stocks_pnl = stocks_df['pnl'].sum()
        # PnL (simplified)
        total_val = sacco_val + bonds_val + crypto_val + mmf_val + stocks_val
        total_pnl = bonds_val + crypto_val + mmf_val + stocks_val + sacco_val - (
            sacco_df['contribution'].sum() if not sacco_df.empty else 0
            + bonds_df['principal'].sum() if not bonds_df.empty else 0
            + crypto_df['amount'].sum() * 0 if not crypto_df.empty else 0
            + (mmf_df['balance'].sum() if not mmf_df.empty else 0)
            + stocks_df['purchase_price'].sum() if not stocks_df.empty else 0
        )
        asset_vals = {
            'SACCO': sacco_val,
            'Bonds': bonds_val,
            'Crypto': crypto_val,
            'MMF': mmf_val,
            'Stocks': stocks_val
        }
        best_asset = max(asset_vals, key=asset_vals.get) if total_val > 0 else '-'
        worst_asset = min(asset_vals, key=asset_vals.get) if total_val > 0 else '-'
        return total_val, total_pnl, best_asset, worst_asset, asset_vals

    total_val, total_pnl, best_asset, worst_asset, asset_vals = get_portfolio_summary()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Portfolio Value (KES)", f"{total_val:,.2f}")
    col2.metric("Total Profit/Loss", f"{total_pnl:,.2f}")
    col3.metric("Best Performing Asset", best_asset)
    col4.metric("Worst Performing Asset", worst_asset)

    # Asset allocation pie chart
    pie_df = pd.DataFrame({"Asset": list(asset_vals.keys()), "Value": list(asset_vals.values())})
    pie_df = pie_df[pie_df['Value'] > 0]
    if not pie_df.empty:
        st.plotly_chart(px.pie(pie_df, names="Asset", values="Value", title="Asset Allocation"), use_container_width=True)
    else:
        st.info("No assets in portfolio yet.")

    # --- End of Year Totals ---
    st.subheader(f"End of Year ({datetime.now().year}) Projected Totals")
    eoy = get_end_of_year_totals()
    eoy_df = pd.DataFrame({"Asset": list(eoy.keys()), "Projected Value": list(eoy.values())})
    st.table(eoy_df)
                    st.experimental_rerun()
with st.sidebar.expander("Money Market Fund"):
    mmf_df = fetch_table('mmf')
    with st.form("mmf_form_sidebar", clear_on_submit=True):
        name = st.text_input("Fund Name", value="Etica Money Market Fund", key="mmf_name")
        balance = st.number_input("Balance (KES)", min_value=0.0, value=0.0, step=100.0, key="mmf_balance")
        annual_rate = st.number_input("Annual Rate (%)", min_value=0.0, value=9.0, step=0.01, key="mmf_rate")
        last_update = st.date_input("Last Update", value=datetime.now(), key="mmf_update")
        submitted = st.form_submit_button("Update MMF")
        if submitted:
            conn = get_connection()
            conn.execute("DELETE FROM mmf")
            conn.execute("INSERT INTO mmf (name, balance, annual_rate, last_update) VALUES (?, ?, ?, ?)", (name, balance, annual_rate, last_update.strftime('%Y-%m-%d')))
            conn.commit()
            conn.close()
            st.success(f"MMF updated: {balance} KES at {annual_rate}% annual rate")
            st.experimental_rerun()
    # Edit/Delete options
    if not mmf_df.empty:
        st.write("#### Edit/Delete MMF")
        for idx, row in mmf_df.iterrows():
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"{row['name']}: {row['balance']} KES @ {row['annual_rate']}%")
            with col2:
                if st.button(f"Delete", key=f"del_mmf_{row['id']}"):
                    conn = get_connection()
                    conn.execute("DELETE FROM mmf WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()
with st.sidebar.expander("Stock"):
    stocks_df = fetch_table('stocks')
    with st.form("stocks_form_sidebar", clear_on_submit=True):
        ticker = st.text_input("Ticker (e.g. KGN.NR, AAPL)", value="KGN.NR", key="stock_ticker")
        shares = st.number_input("Shares", min_value=0.0, value=0.0, step=1.0, key="stock_shares")
        purchase_price = st.number_input("Purchase Price (KES)", min_value=0.0, value=0.0, step=1.0, key="stock_purchase")
        current_price = st.number_input("Current Price (KES)", min_value=0.0, value=0.0, step=1.0, key="stock_current")
        submitted = st.form_submit_button("Add Stock")
        if submitted and shares > 0:
            conn = get_connection()
            conn.execute("INSERT INTO stocks (ticker, shares, purchase_price, current_price) VALUES (?, ?, ?, ?)", (ticker.upper(), shares, purchase_price, current_price))
            conn.commit()
            conn.close()
            st.success(f"Added {shares} shares of {ticker.upper()} at {purchase_price} KES")
            st.experimental_rerun()
    # Edit/Delete options
    if not stocks_df.empty:
        st.write("#### Edit/Delete Stocks")
        for idx, row in stocks_df.iterrows():
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"{row['ticker']}: {row['shares']} @ {row['purchase_price']} KES (Current: {row['current_price']} KES)")
            with col2:
                if st.button(f"Delete", key=f"del_stock_{row['id']}"):
                    conn = get_connection()
                    conn.execute("DELETE FROM stocks WHERE id=?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.experimental_rerun()

# --- Main App Body ---


# --- Main Asset Sections ---
# (All asset entry and display logic is now handled in the sidebar and dashboard sections above)

# --- AI Analytics Section ---
ai_analytics_section()

# --- Footer ---
st.markdown("---")
st.caption("Professional Hedge Fund Terminal for Kenyan Investors | Built with Streamlit, Python, and AI Analytics")
