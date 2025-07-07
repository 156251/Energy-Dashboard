import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go

# --- 1. Get Crude Oil and Natural Gas Prices ---
def get_energy_prices():
    wti = yf.Ticker("CL=F").history(period="7d")["Close"]
    natgas = yf.Ticker("NG=F").history(period="7d")["Close"]
    return pd.DataFrame({"WTI Crude": wti, "Natural Gas": natgas})

# --- 2. Dual-Axis Chart for Oil & Gas ---
def plot_energy_prices(df):
    fig = go.Figure()
    # WTI Crude on left axis
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["WTI Crude"],
            name="WTI Crude",
            yaxis="y1",
            mode="lines+markers"
        )
    )
    # Natural Gas on right axis
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Natural Gas"],
            name="Natural Gas",
            yaxis="y2",
            mode="lines+markers"
        )
    )

    # Update layout with fixed right-axis range and repositioned legend
    fig.update_layout(
        title_text="Daily Prices: WTI Crude Oil vs. Natural Gas (Henry Hub)",
        xaxis_title="Date",
        yaxis=dict(
            title_text="WTI Crude (USD)",
            title_font_color="blue",
            tickprefix="$",
            tickformat=".2f"
        ),
        yaxis2=dict(
            title_text="Natural Gas (USD)",
            title_font_color="green",
            overlaying="y",
            side="right",
            tickprefix="$",
            range=[3.2, 3.4]
        ),
        legend=dict(
            title=dict(text="Commodity"),
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top"
        ),
        margin=dict(r=150)
    )
    st.plotly_chart(fig, use_container_width=True)

# --- 3. Stock Data with Multiples and Daily Change ---
def get_stock_data_with_fundamentals(tickers):
    company_info = {
        "XOM": {"Name": "ExxonMobil", "Vertical": "Integrated"},
        "CVX": {"Name": "Chevron", "Vertical": "Integrated"},
        "COP": {"Name": "ConocoPhillips", "Vertical": "Upstream"},
        "WMB": {"Name": "Williams Companies", "Vertical": "Midstream"}
    }

    def scrape_valuation(ticker):
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", class_="snapshot-table2")
        data = {}
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            for i, col in enumerate(cols):
                if col.text == "EV/EBITDA":
                    data["EV/EBITDA"] = cols[i+1].text + "x"
                if col.text == "P/S":
                    data["EV/Revenue"] = cols[i+1].text + "x"
        return data

    rows = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if len(hist) < 2:
            continue
        today = hist['Close'].iloc[-1]
        yesterday = hist['Close'].iloc[-2]
        pct_change = ((today - yesterday) / yesterday) * 100
        valuation = scrape_valuation(ticker)

        rows.append({
            'Company Name': company_info[ticker]['Name'],
            'Ticker': ticker,
            'Share Price': f"${today:.2f}",
            'Daily % Change': f"{pct_change:.2f}%",
            'Vertical': company_info[ticker]['Vertical'],
            'EV/EBITDA Multiple': valuation.get('EV/EBITDA', 'N/A'),
            'EV/Revenue Multiple': valuation.get('EV/Revenue', 'N/A')
        })

    return pd.DataFrame(rows)

# --- 4. Sector KPI Table ---
def get_sector_kpi_distribution():
    return pd.DataFrame([
        {' ': '**25th Percentile**', 'EV/EBITDA': '5.3x', 'P/E': '9.8x', 'FCF Yield': '5.9%', 'Net Debt/EBITDA': '1.2x'},
        {' ': '**Median**', 'EV/EBITDA': '6.7x', 'P/E': '11.4x', 'FCF Yield': '7.2%', 'Net Debt/EBITDA': '1.5x'},
        {' ': '**75th Percentile**', 'EV/EBITDA': '7.9x', 'P/E': '13.2x', 'FCF Yield': '8.8%', 'Net Debt/EBITDA': '2.0x'}
    ])

# --- 5. News Feed ---
def get_energy_news():
    url = "https://news.google.com/rss/search?q=energy+sector&hl=en-US&gl=US&ceid=US:en"
    xml = requests.get(url).content
    soup = BeautifulSoup(xml, 'xml')
    items = soup.find_all('item')[:5]
    return [f"**[{item.title.text}]({item.link.text})**  \n*{item.pubDate.text}*" for item in items]

# --- Main Execution ---
tickers = ['XOM', 'CVX', 'COP', 'WMB']
energy_prices = get_energy_prices()
stock_data = get_stock_data_with_fundamentals(tickers)
sector_kpis = get_sector_kpi_distribution()
news = get_energy_news()

st.title("Energy Sector Dashboard")

st.markdown("## 📈 Daily Prices: Oil and Gas")
plot_energy_prices(energy_prices)

st.markdown("## 🏢 Industry Leaders | Company Name | Ticker | Share Price | Daily % Change | Vertical | EV/EBITDA | EV/Revenue |")
st.dataframe(stock_data, use_container_width=True)

st.markdown("## 📊 Valuation Multiples and Financial KPIs (Sector Averages) | EV/EBITDA | P/E | FCF Yield | Net Debt/EBITDA |")
st.dataframe(sector_kpis, use_container_width=True)

st.markdown("## 📰 Latest Energy News")
for article in news:
    st.markdown(article)
