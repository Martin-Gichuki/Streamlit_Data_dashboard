# All the necessary imports
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
import warnings
import plotly.figure_factory as ff
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.graph_objects as go
from datasets import load_dataset

warnings.filterwarnings("ignore")

# Page settings
st.set_page_config(
    page_title="Superstore Sales Dashboard",
    page_icon=":bar_chart:",
    layout="wide"
)

# # Theme toggle
# theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])
# if theme == "Light":
#     plotly_template = "plotly_white"
# else:
#     plotly_template = "plotly_dark"

# Title and Intro
st.title(":bar_chart: Superstore Sales Dashboard")
st.markdown("""
Welcome to the **Superstore Sales Dashboard**. This interactive tool allows you to explore key performance indicators such as sales, profit, and quantity across different regions, categories, and customer segments.

Use the filters in the sidebar to focus your analysis.
""")

st.markdown("<style>div.block-container {padding-top: 3rem;}</style>", unsafe_allow_html=True)


# File Upload or Default Load
f1 = st.file_uploader(":file_folder: Upload your file", type=["xls","csv", "xlsx","txt"])
if f1 is not None:
    if f1.name.endswith('.csv'):
        df = pd.read_csv(f1)
    else:
        df = pd.read_excel(f1)
else:
    dataset = load_dataset("1gichukimba/superstores", data_files="superstore.csv", split="train")
    df = pd.DataFrame(dataset)
    st.info("Using default dataset from Hugging Face 🌐")
# Data Preview
st.markdown("""
**🧾 Data Snapshot:**  
Here’s a quick preview of the uploaded Superstore dataset. This helps users validate the input and structure of the data before applying filters or analysis.
""")
st.subheader("📊 Data Preview")
st.dataframe(df.head())

# Date Filter
st.markdown("""
**📅 Filter by Date Range:**  
Use this date range selector to narrow down the analysis to a specific period. This helps uncover trends during promotional seasons, holidays, or financial quarters.
""")

col1, col2 = st.columns(2)
df['Order Date'] = pd.to_datetime(df['Order Date'])
start_date = df['Order Date'].min()
end_date = df['Order Date'].max()
with col1:
    date_1 = pd.to_datetime(st.date_input("Select Start Date", start_date))
with col2:
    date_2 = pd.to_datetime(st.date_input("Select End Date", end_date))
df = df[(df['Order Date'] >= date_1) & (df['Order Date'] <= date_2)]

# Sidebar Filters
st.sidebar.header("Filter Options")
region = st.sidebar.multiselect("Select Region", options=df['Region'].unique())
df2 = df if not region else df[df['Region'].isin(region)]
state = st.sidebar.multiselect("Select State", options=df2['State'].unique())
df3 = df2 if not state else df2[df2['State'].isin(state)]
city = st.sidebar.multiselect("Select City", options=df3['City'].unique())

if not region and not state and not city:
    filtered_df = df.copy()
elif not state and not city:
    filtered_df = df[df['Region'].isin(region)]
elif not region and not city:
    filtered_df = df[df['State'].isin(state)]
elif not region and not state:
    filtered_df = df[df['City'].isin(city)]
elif state and city:
    filtered_df = df3[(df3['State'].isin(state)) & (df3['City'].isin(city))]
elif region and city:
    filtered_df = df3[(df3['Region'].isin(region)) & (df3['City'].isin(city))]
elif region and state:
    filtered_df = df3[(df3['Region'].isin(region)) & (df3['State'].isin(state))]
elif city:
    filtered_df = df3[df3['City'].isin(city)]
else:
    filtered_df = df3[df3['Region'].isin(region) & df3['State'].isin(state) & df3['City'].isin(city)]

# KPIs
st.markdown("""
**📌 Key Metrics Overview:**  
This section provides high-level figures including total sales, total profit, and number of unique orders. It gives a bird’s-eye view of business performance.
""")

col1, col2, col3 = st.columns(3)
col1.metric("Total Sales", f"${filtered_df['Sales'].sum():,.2f}")
col2.metric("Total Profit", f"${filtered_df['Profit'].sum():,.2f}")
col3.metric("Total Orders", filtered_df['Order ID'].nunique())

# Geographic Map
st.markdown("""
**🗺️ Geographic Sales Distribution:**  
This map visualizes city-level sales (if coordinates are available). It helps identify top-performing urban centers geographically.
""")

st.subheader("🗺️ Sales by City (Geographic Map)")
if 'Latitude' in filtered_df.columns and 'Longitude' in filtered_df.columns:
    city_map = filtered_df.groupby(['City', 'Latitude', 'Longitude'], as_index=False)['Sales'].sum()
    fig = px.scatter_mapbox(
        city_map,
        lat="Latitude",
        lon="Longitude",
        size="Sales",
        hover_name="City",
        zoom=3,
        mapbox_style="carto-positron",
        title="Sales by City",
        color_discrete_sequence=["#1f77b4"]
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No latitude/longitude columns found for geographic map visualization.")

plotly_template = "plotly_dark"
# Customer Segment Analysis
st.markdown("""
**👥 Segment-Based Performance:**  
This chart breaks down sales by customer segment and region, helping businesses understand who their best customers are and where they’re located.
""")

st.subheader("👥 Customer Segment Analysis")
segment_df = filtered_df.groupby(['Segment', 'Region'], as_index=False)['Sales'].sum()
fig = px.bar(segment_df, x='Segment', y='Sales', color='Region', barmode='group', template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Sales by Category
st.markdown("""
**🛍️ Sales by Product Category & Region:**  
Compare performance across product categories and regional distributions. Useful for product planning and inventory decisions.
""")

category_df = filtered_df.groupby('Category', as_index=False)['Sales'].sum()
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Sales by Product Category**")
    fig = px.bar(category_df, x='Category', y='Sales', color='Category', text_auto='.2s', template=plotly_template)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("**Sales Distribution by Region**")
    region_df = filtered_df.groupby('Region', as_index=False)['Sales'].sum()
    fig = px.pie(region_df, names='Region', values='Sales', hole=0.3, template=plotly_template)
    st.plotly_chart(fig, use_container_width=True)

# Time Series
st.markdown("""
**📈 Sales Over Time:**  
This line chart tracks monthly sales, making it easy to spot seasonal patterns, growth, or dips over time.
""")

st.subheader("📈 Monthly Sales Trend")
filtered_df['month_year'] = filtered_df['Order Date'].dt.to_period("M")
linechart = filtered_df.groupby(filtered_df['month_year'].dt.strftime('%Y-%m'))['Sales'].sum().reset_index()
fig = px.line(linechart, x='month_year', y='Sales', markers=True, template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# # Forecasting with Prophet
# st.subheader(":crystal_ball: Forecast Sales with Prophet")
# st.markdown("""
# **📈 How to Read the Forecast Chart:**  
# - **Blue line**: historical sales data  
# - **Black dashed line**: predicted sales for the next 30 days  
# - **Shaded region**: confidence interval showing the likely range of values

# Use this forecast to anticipate future trends and make data-informed decisions.
# """)

# prophet_df = df[['Order Date', 'Sales']].rename(columns={'Order Date': 'ds', 'Sales': 'y'})
# model = Prophet()
# model.fit(prophet_df)
# future = model.make_future_dataframe(periods=30)
# forecast = model.predict(future)

# fig4 = plot_plotly(model, forecast)
# fig4.update_layout(template=plotly_template)

# # Style the traces
# for trace in fig4.data:
#     if 'trend' in trace.name.lower():
#         trace.line.color = 'black'
#         trace.line.dash = 'dash'
#     elif 'actual' in trace.name.lower() or 'y' in trace.name.lower():
#         trace.line.color = 'blue'

# st.plotly_chart(fig4, use_container_width=True)


# Treemap
st.markdown("""
**🌲 Sales Breakdown (Treemap):**  
Visualizes sales by Region → Category → Sub-Category in a hierarchical structure. Helpful for understanding the breadth and depth of the product portfolio.
""")

st.subheader("🌎 Sales Hierarchy by Region, Category, and Sub-Category")
fig = px.treemap(
    filtered_df,
    path=['Region', 'Category', 'Sub-Category'],
    values='Sales',
    color='Sub-Category',
    template=plotly_template,
    color_continuous_scale='RdBu',
    hover_data=['Sales']
)
st.plotly_chart(fig, use_container_width=True)

# Segment & Subcategory
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Sales by Segment**")
    fig = px.pie(filtered_df, names='Segment', values='Sales', hole=0.3, template=plotly_template)
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.markdown("**Sales by Sub-Category**")
    fig = px.pie(filtered_df, names='Sub-Category', values='Sales', hole=0.3, template=plotly_template)
    st.plotly_chart(fig, use_container_width=True)

# Scatter Plot
st.markdown("""
**📊 Sales vs Profit:**  
This scatter plot shows how sales and profit are related per order. Large bubbles indicate high quantity sold.
""")

st.subheader("📊 Profitability vs Revenue")
data1 = px.scatter(filtered_df, x='Sales', y='Profit', size='Quantity', template=plotly_template)
data1.update_layout(
    title=dict(text='Sales vs Profit Scatter Plot', font=dict(size=18)),
    xaxis=dict(title=dict(text='Sales', font=dict(size=14))),
    yaxis=dict(title=dict(text='Profit', font=dict(size=14)))
)
st.plotly_chart(data1, use_container_width=True)

# Discount vs Profit
st.markdown("""
**🔥 Discount Effect on Profit:**  
This chart shows the correlation between discount and profitability. Helps detect over-discounting that leads to losses.
""")

st.subheader("🔥 Impact of Discount on Profit")
discount_fig = px.scatter(
    filtered_df, x='Discount', y='Profit', size='Sales', color='Category',
    template=plotly_template, title='Discount vs Profit', hover_data=['Product Name']
)
st.plotly_chart(discount_fig, use_container_width=True)

# Top Products
st.markdown("""
**🏆 Top 10 Products by Sales:**  
Highlights the most revenue-generating products to guide future stock, marketing, and bundling strategies.
""")

st.subheader("👉 Top 10 Products by Sales")
top_products = filtered_df.groupby('Product Name', as_index=False)['Sales'].sum().nlargest(10, 'Sales')
fig = px.bar(top_products, x='Sales', y='Product Name', orientation='h', template=plotly_template)
st.plotly_chart(fig, use_container_width=True)

# Additional Business Insights
st.markdown("""
**📌 Business Insights:**  
Explore deeper performance indicators like total profit by region and average sales per order to refine strategy.
""")

st.subheader("📌 Additional Business Insights")
# Profit by Region
profit_region = filtered_df.groupby('Region', as_index=False)['Profit'].sum()
fig = px.bar(profit_region, x='Region', y='Profit', template=plotly_template, color='Region')
st.plotly_chart(fig, use_container_width=True)

# Sales per Order
order_sales = filtered_df.groupby('Order ID', as_index=False)['Sales'].sum()
fig = px.histogram(order_sales, x='Sales', nbins=30, template=plotly_template, title="Sales per Order")
st.plotly_chart(fig, use_container_width=True)

# Download full filtered data
st.download_button("Download Full Filtered Data", data=filtered_df.to_csv(index=False), file_name="filtered_data.csv")

# Downloadable Summary Table
st.markdown("""
**📋 Monthly Sub-Category Sales Table:**  
This pivot table gives a monthly breakdown of sales across sub-categories. Great for tabular insights and export.
""")

st.subheader("🔍 Monthly Sales by Sub-Category")
with st.expander("View Table"):
    filtered_df['month'] = filtered_df['Order Date'].dt.month_name() + ' ' + filtered_df['Order Date'].dt.year.astype(str)
    sub_category_year = pd.pivot_table(
        data=filtered_df,
        values='Sales',
        index=['Sub-Category'],
        columns='month',
    )
    st.write(sub_category_year.style.background_gradient(cmap='Purples'))
