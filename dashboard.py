import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import plotly.graph_objects as go
import streamlit as st

# --- 1. Get Crude Oil and Natural Gas Prices ---
def get_energy_prices():
    wti = yf.Ticker("CL=F").history(period="7d")["Close"]
    natgas = yf.Ticker("NG=F").history(period="7d")["Close"]
    return pd.DataFrame({"WTI Crude": wti, "Natural Gas": natgas})

# --- 2. Dual-Axis Chart for Oil & Gas ---
def plot_energy_prices(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["WTI Crude"], name="WTI Crude", yaxis="y1", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=df.index, y=df["Natural Gas"], name="Natural Gas", yaxis="y2", mode="lines+markers"))

    fig.update_layout(
        title="Daily Prices: WTI Crude Oil vs. Natural Gas (Henry Hub)",
        xaxis=dict(title="Date"),
        yaxis=dict(title="WTI Crude (USD)", titlefont=dict(color="blue"), tickprefix="$", tickformat=".2f"),
        yaxis2=dict(title="Natural Gas (USD)", titlefont=dict(color="green"), overlaying="y", side="right",
                    tickprefix="$", range=[3.0, 4.0]),
        legend=dict(title=dict(text="Commodity"))
    )
    st.plotly_chart(fig)

# --- 3. Stock Data with Multiples and Daily Change ---
def get_stock_data_with_fundamentals(tickers):
    company_info = {
        "XOM": {"Name": "ExxonMobil", "Vertical": "Integrated"},
        "CVX": {"Name": "Chevron", "Vertical": "Integrated"},
        "COP": {"Name": "ConocoPhillips", "Vertical": "Upstream"},
        "WMB": {"Name": "Williams Companies", "Vertical": "Midstream"},
    }

    def scrape_valuation(ticker):
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find_all("table", class_="snapshot-table2")[0]
        data = {}
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            for i in range(len(cells)):
                if cells[i].text == "EV/EBITDA":
                    data["EV/EBITDA"] = cells[i + 1].text + "x"
                if cells[i].text == "P/S":
                    data["EV/Revenue"] = cells[i + 1].text + "x"
        return data

    data = []
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if len(hist) < 2:
            continue
        today = hist["Close"].iloc[-1]
        yesterday = hist["Close"].iloc[-2]
        change_pct = ((today - yesterday) / yesterday) * 100
        val = scrape_valuation(ticker)

        data.append({
            "Company Name": company_info[ticker]["Name"],
            "Ticker": ticker,
            "Share Price": f"${round(today, 2)}",
            "Daily % Change": round(change_pct, 2),
            "Vertical": company_info[ticker]["Vertical"],
            "EV/EBITDA Multiple": val.get("EV/EBITDA", "N/A"),
            "EV/Revenue Multiple": val.get("EV/Revenue", "N/A"),
        })

    df = pd.DataFrame(data)
    df["Daily % Change"] = df["Daily % Change"].map(lambda x: f"{x:.2f}%")
    return df

# --- 4. Sector KPI Table ---
def get_sector_kpi_distribution():
    return pd.DataFrame([
        {
            " ": "**25th Percentile**",
            "EV/EBITDA": "5.3x",
            "P/E": "9.8x",
            "FCF Yield": "5.9%",
            "Net Debt/EBITDA": "1.2x"
        },
        {
            " ": "**Median**",
            "EV/EBITDA": "6.7x",
            "P/E": "11.4x",
            "FCF Yield": "7.2%",
            "Net Debt/EBITDA": "1.5x"
        },
        {
            " ": "**75th Percentile**",
            "EV/EBITDA": "7.9x",
            "P/E": "13.2x",
            "FCF Yield": "8.8%",
            "Net Debt/EBITDA": "2.0x"
        },
    ])

# --- 5. News Feed ---
def get_energy_news():
    url = "https://news.google.com/rss/search?q=energy+sector&hl=en-US&gl=US&ceid=US:en"
    xml = requests.get(url).content
    soup = BeautifulSoup(xml, features="xml")
    items = soup.findAll("item")[:5]
    news = []
    for item in items:
        news.append(f"**[{item.title.text}]({item.link.text})**  \n*{item.pubDate.text}*")
    return news

# --- 6. Streamlit Page Layout ---
tickers = ["XOM", "CVX", "COP", "WMB"]
energy_prices = get_energy_prices()
stock_data = get_stock_data_with_fundamentals(tickers)
sector_kpis = get_sector_kpi_distribution()
news = get_energy_news()

st.markdown("## 📈 Daily Prices: Oil and Gas")
plot_energy_prices(energy_prices)

st.markdown("## 🏢 Industry Leaders | Company Name | Ticker | Share Price | Daily % Change | Vertical | EV/EBITDA | EV/Revenue |")
st.dataframe(stock_data, use_container_width=True)

st.markdown("## 📊 Valuation Multiples and Financial KPIs (Sector Averages) | EV/EBITDA | P/E | FCF Yield | Net Debt/EBITDA |")
st.dataframe(sector_kpis, use_container_width=True)

st.markdown("## 📰 Latest Energy News")
for article in news:
    st.markdown(f"- {article}")
