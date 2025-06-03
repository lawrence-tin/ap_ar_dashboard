# main.py
import streamlit as st
from snowflake_connector import run_query
import pandas as pd
import altair as alt

# Set config first!
st.set_page_config(page_title="AR/AP Dashboard", layout="wide")
st.title("📊 Accounts Receivable / Payable Dashboard")

# Tabs
tab1, tab2, tab3 = st.tabs(["📥 Accounts Receivable", "📤 Accounts Payable", "📚 Combined Summary"])

# ---------- AR TAB ----------
with tab1:
    st.subheader("Filter AR Invoices")
    ar_date_range = st.date_input("Invoice Date Range", [], key="ar_date")
    customer = st.text_input("Customer Name (optional)")
    ar_status = st.multiselect("Status", ["Paid", "Unpaid", "Partially Paid"], default=["Paid", "Unpaid", "Partially Paid"], key="ar_status")

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
        ar_df.columns = ar_df.columns.str.upper()

        # Add derived fields
        ar_df["DAYS_OVERDUE"] = (pd.to_datetime("today") - pd.to_datetime(ar_df["DUEDATE"])).dt.days
        ar_df["PAST_DUE"] = ar_df["DAYS_OVERDUE"] > 0

        # KPIs
        total_ar = ar_df["INVOICEAMOUNT"].sum()
        outstanding_ar = ar_df[ar_df["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum()
        dso = ar_df["DAYS_OVERDUE"].mean()

        st.metric("📄 Total AR", f"${total_ar:,.2f}")
        st.metric("💰 Outstanding AR", f"${outstanding_ar:,.2f}")
        st.metric("📆 DSO (Avg Days Outstanding)", f"{dso:.1f} days")

        # Aging buckets
        aging_bins = [0, 30, 60, 90, 9999]
        aging_labels = ["0-30", "31-60", "61-90", "90+"]
        ar_df["AGING_BUCKET"] = pd.cut(ar_df["DAYS_OVERDUE"], bins=aging_bins, labels=aging_labels, right=False)

        ar_chart = alt.Chart(ar_df).mark_bar().encode(
            x=alt.X("CUSTOMERNAME", sort='-y'),
            y="INVOICEAMOUNT",
            color="STATUS"
        ).properties(width=600, height=300, title="AR by Customer")

        aging_chart = alt.Chart(ar_df).mark_bar().encode(
            x="AGING_BUCKET",
            y="INVOICEAMOUNT",
            color="STATUS"
        ).properties(width=400, height=300, title="Aging Buckets (AR)")

        st.altair_chart(ar_chart, use_container_width=True)
        st.altair_chart(aging_chart, use_container_width=True)

        st.dataframe(ar_df)
    else:
        st.info("No AR data found for the filters provided.")

    # Download Button for AR
    csv_ar = ar_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download AR Data as CSV",
        data=csv_ar,
        file_name='AR_invoices.csv',
        mime='text/csv',
    )

    # Alert: High Overdue AR
    overdue_threshold = 50000
    overdue_total = ar_df[ar_df["PAST_DUE"]]["INVOICEAMOUNT"].sum()

    if overdue_total > overdue_threshold:
        st.warning(f"⚠️ High overdue AR detected! ${overdue_total:,.2f} is past due.")

# ---------- AP TAB ----------
with tab2:
    st.subheader("Filter AP Invoices")
    ap_date_range = st.date_input("Invoice Date Range (AP)", [], key="ap_date")
    vendor = st.text_input("Vendor Name (optional)")
    ap_status = st.multiselect("Status", ["Paid", "Unpaid", "Partially Paid"], default=["Paid", "Unpaid", "Partially Paid"], key="ap_status")

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
        ap_df["DAYS_OVERDUE"] = (pd.to_datetime("today") - pd.to_datetime(ap_df["DUEDATE"])).dt.days
        ap_df["PAST_DUE"] = ap_df["DAYS_OVERDUE"] > 0

        total_ap = ap_df["INVOICEAMOUNT"].sum()
        outstanding_ap = ap_df[ap_df["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum()
        dpo = ap_df["DAYS_OVERDUE"].mean()

        st.metric("📄 Total AP", f"${total_ap:,.2f}")
        st.metric("💸 Outstanding AP", f"${outstanding_ap:,.2f}")
        st.metric("📆 DPO (Avg Days Payable)", f"{dpo:.1f} days")

        # Aging buckets
        aging_bins = [0, 30, 60, 90, 9999]
        aging_labels = ["0-30", "31-60", "61-90", "90+"]
        ap_df["AGING_BUCKET"] = pd.cut(ap_df["DAYS_OVERDUE"], bins=aging_bins, labels=aging_labels, right=False)

        ap_chart = alt.Chart(ap_df).mark_bar().encode(
            x=alt.X("VENDORNAME", sort='-y'),
            y="INVOICEAMOUNT",
            color="STATUS"
        ).properties(width=600, height=300, title="AP by Vendor")

        aging_chart = alt.Chart(ap_df).mark_bar().encode(
            x="AGING_BUCKET",
            y="INVOICEAMOUNT",
            color="STATUS"
        ).properties(width=400, height=300, title="Aging Buckets (AP)")

        st.altair_chart(ap_chart, use_container_width=True)
        st.altair_chart(aging_chart, use_container_width=True)

        st.dataframe(ap_df)
    else:
        st.info("No AP data found for the filters provided.")

    # Download Button for AP
    csv_ap = ap_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download AP Data as CSV",
        data=csv_ap,
        file_name='AP_invoices.csv',
        mime='text/csv',
    )

    # Alert: High Outstanding Payables
    ap_alert_threshold = 40000
    if outstanding_ap > ap_alert_threshold:
        st.error(f"🔴 Outstanding AP exceeds threshold! Current: ${outstanding_ap:,.2f}")


# ---------- COMBINED SUMMARY ----------
with tab3:
    st.subheader("📚 Combined AR/AP Summary")

    # Fetch latest AR & AP
    ar_df = run_query("SELECT * FROM AR_INVOICES")
    ap_df = run_query("SELECT * FROM AP_INVOICES")

    if isinstance(ar_df, pd.DataFrame) and isinstance(ap_df, pd.DataFrame):
        ar_df.columns = ar_df.columns.str.upper()
        ap_df.columns = ap_df.columns.str.upper()

        ar_total = ar_df["INVOICEAMOUNT"].sum()
        ap_total = ap_df["INVOICEAMOUNT"].sum()
        balance = ar_total - ap_total

        status = "Surplus" if balance >= 0 else "Deficit"
        color = "🟢" if balance >= 0 else "🔴"

        st.metric("💼 Balance (AR - AP)", f"${balance:,.2f}", delta=status)

        st.metric("📥 Total Receivables", f"${ar_total:,.2f}")
        st.metric("📤 Total Payables", f"${ap_total:,.2f}")
    else:
        st.warning("Could not load combined data.")
