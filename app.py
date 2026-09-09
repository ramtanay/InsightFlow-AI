import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pandasai as pai
from pandasai_litellm.litellm import LiteLLM

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* Main background */
    .stApp {
        background-color: #f7f9fc;
    }

    /* Header */
    .main-header {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
        color: #111827;
    }

    .sub-header {
        color: #6b7280;
        font-size: 17px;
        margin-bottom: 25px;
    }

    /* KPI cards */
    .kpi-card {
        background: white;
        padding: 22px;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.05);
        min-height: 130px;
    }

    .kpi-title {
        color: #6b7280;
        font-size: 14px;
        font-weight: 600;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 800;
        color: #111827;
        margin-top: 8px;
    }

    .kpi-icon {
        font-size: 25px;
    }

    /* Section headers */
    .section-title {
        font-size: 24px;
        font-weight: 750;
        color: #111827;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* AI box */
    .ai-box {
        background: linear-gradient(
            135deg,
            #eef2ff,
            #f5f3ff
        );
        border: 1px solid #c7d2fe;
        border-radius: 15px;
        padding: 20px;
        margin-top: 15px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-header">📊 AI Sales Analytics</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-header">'
    'Transform your sales data into insights using Gemini + PandasAI.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## ⚙️ Dashboard Settings")

    st.markdown("---")

    api_key = st.text_input(
        "🔑 Gemini API Key",
        type="password",
        help="Enter your Gemini API key."
    )

    st.markdown("---")

    st.markdown("### 📁 Upload Dataset")

    uploaded_file = st.file_uploader(
        "Upload your sales CSV",
        type=["csv"]
    )

    st.markdown("---")

    st.markdown("### 🎨 Dashboard")

    show_raw_data = st.checkbox(
        "Show raw dataset",
        value=False
    )

    show_charts = st.checkbox(
        "Show charts",
        value=True
    )

    st.markdown("---")

    st.caption("🤖 Powered by Gemini + PandasAI")


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_default_data():

    try:
        return pd.read_csv("sales_data.csv")

    except FileNotFoundError:
        return None


if uploaded_file is not None:

    data = pd.read_csv(uploaded_file)

else:

    data = load_default_data()


# ============================================================
# NO DATA
# ============================================================

if data is None:

    st.warning(
        "📂 No dataset found. Please upload a CSV file from the sidebar."
    )

    st.stop()


# ============================================================
# CLEAN DATA
# ============================================================

data = data.copy()

data.columns = (
    data.columns
    .str.strip()
    .str.replace(" ", "_")
)


# ============================================================
# DETECT IMPORTANT COLUMNS
# ============================================================

def find_column(possible_names):

    for column in data.columns:

        if column.lower() in [
            name.lower()
            for name in possible_names
        ]:
            return column

    return None


quantity_col = find_column(
    ["Quantity", "Qty", "Units", "UnitsSold"]
)

price_col = find_column(
    ["UnitPrice", "Price", "Unit_Price"]
)

revenue_col = find_column(
    ["Revenue", "Sales", "TotalSales", "Amount"]
)

product_col = find_column(
    ["Product", "ProductName", "Item"]
)

city_col = find_column(
    ["City", "Location"]
)

salesperson_col = find_column(
    ["Salesperson", "SalesPerson", "Employee"]
)

date_col = find_column(
    ["Date", "OrderDate", "SalesDate"]
)

order_col = find_column(
    ["OrderID", "Order_Id", "Order"]
)


# ============================================================
# CALCULATE REVENUE
# ============================================================

if revenue_col is not None:

    data["CalculatedRevenue"] = pd.to_numeric(
        data[revenue_col],
        errors="coerce"
    )

elif quantity_col is not None and price_col is not None:

    data["CalculatedRevenue"] = (
        pd.to_numeric(data[quantity_col], errors="coerce")
        *
        pd.to_numeric(data[price_col], errors="coerce")
    )

else:

    data["CalculatedRevenue"] = 0


data["CalculatedRevenue"] = (
    pd.to_numeric(
        data["CalculatedRevenue"],
        errors="coerce"
    ).fillna(0)
)


# ============================================================
# DATA QUALITY
# ============================================================

with st.expander("🧹 Data Quality Check"):

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Rows",
            f"{len(data):,}"
        )

    with col2:
        st.metric(
            "Columns",
            len(data.columns)
        )

    with col3:
        st.metric(
            "Missing Values",
            int(data.isnull().sum().sum())
        )

    with col4:
        st.metric(
            "Duplicate Rows",
            int(data.duplicated().sum())
        )


# ============================================================
# FILTERS
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Filters</div>',
    unsafe_allow_html=True
)

filtered_data = data.copy()

filter_columns = st.columns(4)

# City filter
if city_col:

    with filter_columns[0]:

        cities = sorted(
            data[city_col]
            .dropna()
            .astype(str)
            .unique()
        )

        selected_cities = st.multiselect(
            "🏙️ City",
            cities
        )

        if selected_cities:

            filtered_data = filtered_data[
                filtered_data[city_col]
                .astype(str)
                .isin(selected_cities)
            ]


# Product filter
if product_col:

    with filter_columns[1]:

        products = sorted(
            data[product_col]
            .dropna()
            .astype(str)
            .unique()
        )

        selected_products = st.multiselect(
            "📦 Product",
            products
        )

        if selected_products:

            filtered_data = filtered_data[
                filtered_data[product_col]
                .astype(str)
                .isin(selected_products)
            ]


# Salesperson filter
if salesperson_col:

    with filter_columns[2]:

        people = sorted(
            data[salesperson_col]
            .dropna()
            .astype(str)
            .unique()
        )

        selected_people = st.multiselect(
            "👤 Salesperson",
            people
        )

        if selected_people:

            filtered_data = filtered_data[
                filtered_data[salesperson_col]
                .astype(str)
                .isin(selected_people)
            ]


# Date filter
if date_col:

    with filter_columns[3]:

        filtered_data[date_col] = pd.to_datetime(
            filtered_data[date_col],
            errors="coerce"
        )

        min_date = filtered_data[date_col].min()
        max_date = filtered_data[date_col].max()

        if pd.notna(min_date) and pd.notna(max_date):

            date_range = st.date_input(
                "📅 Date Range",
                value=(min_date.date(), max_date.date())
            )

            if len(date_range) == 2:

                start_date, end_date = date_range

                filtered_data = filtered_data[
                    (filtered_data[date_col].dt.date >= start_date)
                    &
                    (filtered_data[date_col].dt.date <= end_date)
                ]


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_revenue = filtered_data["CalculatedRevenue"].sum()

total_quantity = (
    pd.to_numeric(
        filtered_data[quantity_col],
        errors="coerce"
    ).sum()
    if quantity_col
    else 0
)

if order_col:

    total_orders = filtered_data[order_col].nunique()

else:

    total_orders = len(filtered_data)


if total_orders > 0:

    average_order_value = total_revenue / total_orders

else:

    average_order_value = 0


# ============================================================
# KPI CARDS
# ============================================================

st.markdown(
    '<div class="section-title">📈 Sales Overview</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4 = st.columns(4)


with k1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">💰</div>
            <div class="kpi-title">TOTAL REVENUE</div>
            <div class="kpi-value">₹{total_revenue:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">🛒</div>
            <div class="kpi-title">TOTAL ORDERS</div>
            <div class="kpi-value">{total_orders:,}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">📦</div>
            <div class="kpi-title">UNITS SOLD</div>
            <div class="kpi-value">{total_quantity:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">💳</div>
            <div class="kpi-title">AVERAGE ORDER VALUE</div>
            <div class="kpi-value">₹{average_order_value:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# CHARTS
# ============================================================

if show_charts:

    st.markdown(
        '<div class="section-title">📊 Sales Analytics</div>',
        unsafe_allow_html=True
    )

    chart_col1, chart_col2 = st.columns(2)

    # --------------------------------------------------------
    # Product Revenue
    # --------------------------------------------------------

    if product_col:

        product_sales = (
            filtered_data
            .groupby(product_col)["CalculatedRevenue"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig = px.bar(
            product_sales,
            x="CalculatedRevenue",
            y=product_col,
            orientation="h",
            title="🏆 Top Products by Revenue",
            text_auto=".2s"
        )

        fig.update_layout(
            height=450,
            xaxis_title="Revenue",
            yaxis_title="Product",
            template="plotly_white"
        )

        chart_col1.plotly_chart(
            fig,
            use_container_width=True
        )


    # --------------------------------------------------------
    # City Revenue
    # --------------------------------------------------------

    if city_col:

        city_sales = (
            filtered_data
            .groupby(city_col)["CalculatedRevenue"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )

        fig2 = px.bar(
            city_sales,
            x=city_col,
            y="CalculatedRevenue",
            title="🏙️ Revenue by City",
            text_auto=".2s"
        )

        fig2.update_layout(
            height=450,
            template="plotly_white"
        )

        chart_col2.plotly_chart(
            fig2,
            use_container_width=True
        )


    # --------------------------------------------------------
    # Salesperson
    # --------------------------------------------------------

    if salesperson_col:

        person_sales = (
            filtered_data
            .groupby(salesperson_col)["CalculatedRevenue"]
            .sum()
            .sort_values(ascending=False)
            .reset_index()
        )

        fig3 = px.bar(
            person_sales,
            x=salesperson_col,
            y="CalculatedRevenue",
            title="👤 Salesperson Performance",
            text_auto=".2s"
        )

        fig3.update_layout(
            height=450,
            template="plotly_white"
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )


    # --------------------------------------------------------
    # Time Series
    # --------------------------------------------------------

    if date_col:

        time_data = filtered_data.copy()

        time_data[date_col] = pd.to_datetime(
            time_data[date_col],
            errors="coerce"
        )

        time_data = (
            time_data
            .dropna(subset=[date_col])
            .groupby(date_col)["CalculatedRevenue"]
            .sum()
            .reset_index()
        )

        if not time_data.empty:

            fig4 = px.line(
                time_data,
                x=date_col,
                y="CalculatedRevenue",
                title="📅 Revenue Trend",
                markers=True
            )

            fig4.update_layout(
                height=450,
                template="plotly_white"
            )

            st.plotly_chart(
                fig4,
                use_container_width=True
            )


# ============================================================
# TOP PERFORMERS
# ============================================================

st.markdown(
    '<div class="section-title">🏆 Top Performers</div>',
    unsafe_allow_html=True
)

top_col1, top_col2, top_col3 = st.columns(3)


if product_col:

    with top_col1:

        top_product = (
            filtered_data
            .groupby(product_col)["CalculatedRevenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if not top_product.empty:

            st.success(
                f"🥇 **Best Product**\n\n"
                f"### {top_product.index[0]}\n\n"
                f"Revenue: ₹{top_product.iloc[0]:,.2f}"
            )


if city_col:

    with top_col2:

        top_city = (
            filtered_data
            .groupby(city_col)["CalculatedRevenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if not top_city.empty:

            st.info(
                f"🏙️ **Best City**\n\n"
                f"### {top_city.index[0]}\n\n"
                f"Revenue: ₹{top_city.iloc[0]:,.2f}"
            )


if salesperson_col:

    with top_col3:

        top_person = (
            filtered_data
            .groupby(salesperson_col)["CalculatedRevenue"]
            .sum()
            .sort_values(ascending=False)
        )

        if not top_person.empty:

            st.warning(
                f"👤 **Best Salesperson**\n\n"
                f"### {top_person.index[0]}\n\n"
                f"Revenue: ₹{top_person.iloc[0]:,.2f}"
            )


# ============================================================
# AI ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">🤖 AI Sales Analyst</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="ai-box">
    <b>Ask your data anything.</b><br>
    Gemini will analyze the dataset and answer your question
    using PandasAI.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# PREDEFINED QUESTIONS
# ============================================================

questions = {

    "💰 Total Revenue":
        "Calculate the total revenue. Revenue is Quantity multiplied by UnitPrice.",

    "💳 Average Order Value":
        "Calculate the average order value using Quantity multiplied by UnitPrice.",

    "🏆 Best Product":
        "Find the product generating the highest total revenue.",

    "🏙️ Best City":
        "Find the city generating the highest total revenue.",

    "👤 Best Salesperson":
        "Find the salesperson generating the highest total revenue.",

    "📦 Most Sold Product":
        "Find the product with the highest total quantity sold.",

    "📈 Revenue Trend":
        "Analyze the revenue trend and explain whether sales are increasing or decreasing.",

    "🔍 Business Insights":
        "Analyze the sales dataset and provide five important business insights."
}


selected_question = st.selectbox(
    "Choose an analysis",
    list(questions.keys())
)


if st.button(
    "🚀 Run AI Analysis",
    use_container_width=True
):

    if not api_key:

        st.warning(
            "🔑 Please enter your Gemini API key in the sidebar."
        )

    else:

        with st.spinner(
            "🤖 Gemini is analyzing your sales data..."
        ):

            try:

                llm = LiteLLM(
                    model="gemini/gemini-2.5-flash",
                    api_key=api_key
                )

                pai.config.set({
                    "llm": llm
                })

                df_ai = pai.DataFrame(
                    filtered_data
                )

                result = df_ai.chat(
                    questions[selected_question]
                )

                st.success(
                    "Analysis completed!"
                )

                st.markdown(
                    "### 🤖 AI Result"
                )

                st.write(result)

            except Exception as e:

                st.error(
                    f"❌ AI Error: {str(e)}"
                )


# ============================================================
# CUSTOM AI QUESTION
# ============================================================

st.markdown(
    "### 💬 Ask Your Own Question"
)

custom_question = st.text_input(
    "Ask something about your sales data",
    placeholder="Example: Which city sold the most laptops?"
)


if st.button(
    "🧠 Ask Gemini",
    use_container_width=True
):

    if not api_key:

        st.warning(
            "🔑 Please enter your Gemini API key."
        )

    elif not custom_question:

        st.warning(
            "✍️ Please enter a question."
        )

    else:

        with st.spinner(
            "🧠 Gemini is thinking..."
        ):

            try:

                llm = LiteLLM(
                    model="gemini/gemini-2.5-flash",
                    api_key=api_key
                )

                pai.config.set({
                    "llm": llm
                })

                df_ai = pai.DataFrame(
                    filtered_data
                )

                result = df_ai.chat(
                    custom_question
                )

                st.markdown(
                    "### 🤖 AI Answer"
                )

                st.write(result)

            except Exception as e:

                st.error(
                    f"❌ Error: {str(e)}"
                )


# ============================================================
# DATASET
# ============================================================

if show_raw_data:

    st.markdown(
        '<div class="section-title">📁 Dataset Explorer</div>',
        unsafe_allow_html=True
    )

    st.dataframe(
        filtered_data,
        use_container_width=True,
        height=450
    )

    # Download button

    csv = filtered_data.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Download Filtered Dataset",
        data=csv,
        file_name="filtered_sales_data.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <center>
    <small>
    📊 AI Sales Analytics Dashboard |
    Gemini + PandasAI + Streamlit
    </small>
    </center>
    """,
    unsafe_allow_html=True
)