# main.py
import streamlit as st
from snowflake_connector import run_query
import pandas as pd
import altair as alt

# MUST be first command
st.set_page_config(page_title="AR/AP Dashboard", layout="wide")
st.title("📊 Accounts Receivable / Payable Dashboard")

# Tabs
tab1, tab2 = st.tabs(["📥 Accounts Receivable", "📤 Accounts Payable"])

# -------------------- AR TAB --------------------
with tab1:
    st.subheader("Filter AR Invoices")
    ar_date_range = st.date_input("Invoice Date Range", [], key="ar_date")
    customer = st.text_input("Customer Name (optional)")
    ar_status = st.multiselect("Status", ["Paid", "Unpaid", "Partially Paid"], default=["Paid", "Unpaid", "Partially Paid"], key="ar_status")

    # Build AR query
    ar_query = "SELECT * FROM AR_INVOICES WHERE 1=1"
    if ar_date_range and len(ar_date_range) == 2:
        ar_query += f" AND INVOICEDATE BETWEEN '{ar_date_range[0]}' AND '{ar_date_range[1]}'"
    if customer:
        ar_query += f" AND CUSTOMERNAME ILIKE '%{customer}%'"
    if ar_status:
        formatted_status = "', '".join(ar_status)
        ar_query += f" AND STATUS IN ('{formatted_status}')"

    ar_df = run_query(ar_query)

    if isinstance(ar_df, pd.DataFrame) and not ar_df.empty:
        ar_df.columns = ar_df.columns.str.upper()  # Normalize
        # KPIs
        total_invoices = len(ar_df)
        total_outstanding = ar_df[ar_df["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum()
        avg_days_outstanding = (pd.to_datetime("today") - pd.to_datetime(ar_df["DUEDATE"])).dt.days.mean()

        st.metric("📄 Total AR Invoices", total_invoices)
        st.metric("💰 Total Outstanding", f"${total_outstanding:,.2f}")
        st.metric("📆 Avg Days Outstanding (DSO)", f"{avg_days_outstanding:.1f} days")

        # Charts
        ar_bar = alt.Chart(ar_df).mark_bar().encode(
            x=alt.X("CUSTOMERNAME", sort='-y'),
            y="INVOICEAMOUNT",
            color="STATUS"
        ).properties(width=600, height=300, title="AR by Customer")

        st.altair_chart(ar_bar)

        # Table
        st.dataframe(ar_df)
    else:
        st.info("No AR invoices found for the selected filters.")

# -------------------- AP TAB --------------------
with tab2:
    st.subheader("Filter AP Invoices")
    ap_date_range = st.date_input("Invoice Date Range (AP)", [], key="ap_date")
    vendor = st.text_input("Vendor Name (optional)")
    ap_status = st.multiselect("Status", ["Paid", "Unpaid", "Partially Paid"], default=["Paid", "Unpaid", "Partially Paid"], key="ap_status")

    # Build AP query
    ap_query = "SELECT * FROM AP_INVOICES WHERE 1=1"
    if ap_date_range and len(ap_date_range) == 2:
        ap_query += f" AND INVOICEDATE BETWEEN '{ap_date_range[0]}' AND '{ap_date_range[1]}'"
    if vendor:
        ap_query += f" AND VENDORNAME ILIKE '%{vendor}%'"
    if ap_status:
        formatted_status = "', '".join(ap_status)
        ap_query += f" AND STATUS IN ('{formatted_status}')"

    ap_df = run_query(ap_query)

    if isinstance(ap_df, pd.DataFrame) and not ap_df.empty:
        ap_df.columns = ap_df.columns.str.upper()
        # KPIs
        total_bills = len(ap_df)
        total_payable = ap_df[ap_df["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum()
        avg_days_payable = (pd.to_datetime("today") - pd.to_datetime(ap_df["DUEDATE"])).dt.days.mean()

        st.metric("📄 Total AP Invoices", total_bills)
        st.metric("💸 Total Payables", f"${total_payable:,.2f}")
        st.metric("📆 Avg Days Payable (DPO)", f"{avg_days_payable:.1f} days")

        # Charts
        ap_bar = alt.Chart(ap_df).mark_bar().encode(
            x=alt.X("VENDORNAME", sort='-y'),
            y="INVOICEAMOUNT",
            color="STATUS"
        ).properties(width=600, height=300, title="AP by Vendor")

        st.altair_chart(ap_bar)

        # Table
        st.dataframe(ap_df)
    else:
        st.info("No AP invoices found for the selected filters.")
