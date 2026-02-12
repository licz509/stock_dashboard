import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="📊 A股看板", layout="wide")
st.title("📊 A股低估值股票看板（2026真实数据）")

# --- 侧边栏筛选条件 ---
st.sidebar.header("🔍 筛选条件")
max_pe = st.sidebar.slider("📌 最大市盈率 (PE)", 5, 30, 20)

# --- 从 SQLite 读取数据 ---
conn = sqlite3.connect(r"C:\Users\licz\stock_analysis\a_stock.db")
df_all = pd.read_sql_query(
    f"SELECT stock_code, stock_name, pe, volume FROM a_stock_data WHERE pe <= {max_pe}",
    conn
)
conn.close()

if df_all.empty:
    st.warning("⚠️ 当前没有符合条件的股票，请调整筛选条件。")
    st.stop()

df_all.columns = ["代码", "名称", "PE", "成交额(万元)"]

# --- 多选框选择股票 ---
selected = st.sidebar.multiselect(
    "📌 选择要显示的股票（不选则显示全部）",
    options=df_all["代码"],
    default=df_all["代码"].tolist()
)

# --- 根据选择过滤数据 ---
if selected:
    df = df_all[df_all["代码"].isin(selected)]
else:
    df = df_all

# 修复警告：use_container_width -> width='stretch'
st.dataframe(df, width='stretch')

# --- 图表切换 ---
chart = st.selectbox("📈 选择图表", ["成交额柱状图", "PE折线图", "相关性散点图", "历史PE走势"])

if chart == "成交额柱状图":
    fig, ax = plt.subplots()
    ax.bar(df["代码"], df["成交额(万元)"], color="skyblue")
    ax.set_title(f"📊 成交额对比（PE ≤ {max_pe}）")
    ax.set_xlabel("股票代码")
    ax.set_ylabel("成交额（万元）")
    ax.tick_params(axis="x", rotation=45)
    st.pyplot(fig)

elif chart == "PE折线图":
    fig, ax = plt.subplots()
    ax.plot(df["代码"], df["PE"], marker="o", color="red")
    ax.set_title(f"📉 PE走势（PE ≤ {max_pe}）")
    ax.set_xlabel("股票代码")
    ax.set_ylabel("市盈率")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

elif chart == "相关性散点图":
    fig, ax = plt.subplots()
    ax.scatter(df["PE"], df["成交额(万元)"], color="green", s=60)
    ax.set_title(f"🔗 PE vs 成交额（PE ≤ {max_pe}）")
    ax.set_xlabel("市盈率")
    ax.set_ylabel("成交额（万元）")
    for _, row in df.iterrows():
        ax.text(row["PE"] + 0.2, row["成交额(万元)"] + 1000, row["代码"])
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

else:  # 历史PE走势
    st.subheader("📈 个股历史PE走势")
    if len(df) > 0:
        # 让用户选择具体哪只股票
        selected_stock = st.selectbox(
            "选择股票查看历史PE",
            options=df["代码"],
            format_func=lambda x: f"{x} - {df[df['代码']==x]['名称'].values[0]}"
        )
        stock_code = selected_stock
        stock_name = df[df["代码"] == stock_code]["名称"].values[0]

        if stock_code.startswith("6"):
            symbol = f"{stock_code}.SH"
        else:
            symbol = f"{stock_code}.SZ"

        with st.spinner(f"正在获取 {stock_name}({stock_code}) 的历史PE数据..."):
            try:
                # 获取最近60个交易日的PE数据
                hist_pe = ak.stock_a_pe(symbol=symbol, start_date="20250101", end_date="20260212")
                if hist_pe.empty:
                    st.warning("未获取到历史PE数据")
                else:
                    hist_pe = hist_pe.tail(60)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(hist_pe["date"], hist_pe["pe"], color="orange", marker=".")
                    ax.set_title(f"{stock_name}（{stock_code}）历史PE走势（近60日）")
                    ax.set_xlabel("日期")
                    ax.set_ylabel("市盈率")
                    ax.tick_params(axis="x", rotation=45)
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
            except Exception as e:
                st.error(f"获取历史PE数据失败: {str(e)[:100]}")
    else:
        st.warning("请先选择至少一只股票")

st.caption("📌 数据来源：2026年同花顺·东方财富  |  筛选、多选实时生效  |  历史PE来自AkShare")