# main.py
import streamlit as st
from snowflake_connector import run_query
import pandas as pd
import altair as alt

# Set Streamlit config and dark theme
st.set_page_config(page_title="AR/AP Dashboard", layout="wide")

# Inject custom CSS for styling
st.markdown("""
    <style>
        /* Light blue background */
        body {
            background-color: #e6f0ff;
        }

        .stApp {
            background-color: #e6f0ff;
            padding: 1rem;
        }

        /* Metric card styling */
        .stMetric {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 12px;
            box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.05);
            margin-bottom: 1rem;
        }

        /* Tabs container (sticky nav bar) */
        .stTabs [role="tablist"] {
            background-color: #cce0ff;
            border-radius: 12px;
            padding: 8px;
            position: sticky;
            top: 0;
            z-index: 999;
            box-shadow: 0px 2px 6px rgba(0, 0, 0, 0.1);
        }

        /* Smooth scroll behavior */
        html {
            scroll-behavior: smooth;
        }

        /* Widgets spacing */
        .stTextInput, .stDateInput, .stMultiSelect {
            margin-bottom: 1rem;
        }

        .stDownloadButton {
            margin-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)


st.title("📊 Accounts Receivable / Payable Dashboard")

# Tabs
tabs = st.tabs([
    "📥 Accounts Receivable", "📤 Accounts Payable", "📚 Combined Summary",
    "🚨 Top Overdue Customers", "📆 Aged Receivables",
    "📉 Forecasted Impact", "📦 Top Vendors", "📆 DSO / DPO Analysis"
])
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = tabs

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
        ar_df["DAYS_OVERDUE"] = (pd.to_datetime("today") - pd.to_datetime(ar_df["DUEDATE"])).dt.days
        ar_df["PAST_DUE"] = ar_df["DAYS_OVERDUE"] > 0

        # KPIs
        total_ar = ar_df["INVOICEAMOUNT"].sum()
        outstanding_ar = ar_df[ar_df["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum()
        dso = ar_df["DAYS_OVERDUE"].mean()

        k1, k2, k3 = st.columns(3)
        k1.metric("📄 Total AR", f"${total_ar:,.2f}")
        k2.metric("💰 Outstanding AR", f"${outstanding_ar:,.2f}")
        k3.metric("📆 DSO", f"{dso:.1f} days")

        # Charts
        aging_bins = [0, 30, 60, 90, 9999]
        aging_labels = ["0-30", "31-60", "61-90", "90+"]
        ar_df["AGING_BUCKET"] = pd.cut(ar_df["DAYS_OVERDUE"], bins=aging_bins, labels=aging_labels, right=False)

        c1, c2 = st.columns(2)
        with c1:
            st.altair_chart(
                alt.Chart(ar_df).mark_bar().encode(
                    x=alt.X("CUSTOMERNAME:N", sort='-y'),
                    y="INVOICEAMOUNT:Q",
                    color="STATUS:N"
                ).properties(height=300, title="AR by Customer"),
                use_container_width=True
            )
        with c2:
            st.altair_chart(
                alt.Chart(ar_df).mark_bar().encode(
                    x="AGING_BUCKET:N",
                    y="INVOICEAMOUNT:Q",
                    color="STATUS:N"
                ).properties(height=300, title="Aging Buckets"),
                use_container_width=True
            )

        st.dataframe(ar_df, use_container_width=True)

        st.download_button("⬇️ Download AR Data", ar_df.to_csv(index=False), "AR_invoices.csv", "text/csv")

        overdue_total = ar_df[ar_df["PAST_DUE"]]["INVOICEAMOUNT"].sum()
        if overdue_total > 50000:
            st.warning(f"⚠️ Overdue AR exceeds threshold! ${overdue_total:,.2f}")
    else:
        st.info("No AR data found for the filters provided.")

# ---------- AP TAB ----------
with tab2:
    st.subheader("Filter AP Invoices")
    ap_date_range = st.date_input("Invoice Date Range (AP)", [], key="ap_date")
    vendor = st.text_input("Vendor Name (optional)")
    ap_status = st.multiselect("Status", ["Paid", "Unpaid", "Partially Paid"], default=["Paid", "Unpaid", "Partially Paid"], key="ap_status")

    ap_query = "SELECT * FROM APINVOICES WHERE 1=1"
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

        c1, c2, c3 = st.columns(3)
        c1.metric("📄 Total AP", f"${total_ap:,.2f}")
        c2.metric("💸 Outstanding AP", f"${outstanding_ap:,.2f}")
        c3.metric("📆 DPO", f"{dpo:.1f} days")

        # Charts
        ap_df["AGING_BUCKET"] = pd.cut(ap_df["DAYS_OVERDUE"], bins=aging_bins, labels=aging_labels, right=False)

        c1, c2 = st.columns(2)
        with c1:
            st.altair_chart(
                alt.Chart(ap_df).mark_bar().encode(
                    x=alt.X("VENDORNAME:N", sort='-y'),
                    y="INVOICEAMOUNT:Q",
                    color="STATUS:N"
                ).properties(height=300, title="AP by Vendor"),
                use_container_width=True
            )
        with c2:
            st.altair_chart(
                alt.Chart(ap_df).mark_bar().encode(
                    x="AGING_BUCKET:N",
                    y="INVOICEAMOUNT:Q",
                    color="STATUS:N"
                ).properties(height=300, title="Aging Buckets"),
                use_container_width=True
            )

        st.dataframe(ap_df, use_container_width=True)

        st.download_button("⬇️ Download AP Data", ap_df.to_csv(index=False), "AP_invoices.csv", "text/csv")

        if outstanding_ap > 40000:
            st.error(f"🔴 Outstanding AP exceeds threshold! ${outstanding_ap:,.2f}")
    else:
        st.info("No AP data found for the filters provided.")

# ---------- COMBINED SUMMARY ----------
with tab3:
    st.subheader("📚 Combined AR/AP Summary")

    if 'ar_df' in locals() and 'ap_df' in locals():
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

# ---------- TOP OVERDUE CUSTOMERS ----------
with tab4:
    st.subheader("🚨 Top Overdue Customers")

    if 'ar_df' in locals():
        overdue_df = ar_df[(ar_df["STATUS"] != "Paid") & (pd.to_datetime(ar_df["DUEDATE"]) < pd.Timestamp.today())].copy()
        if overdue_df.empty:
            st.success("✅ No overdue invoices.")
        else:
            overdue_df["DAYS_PAST_DUE"] = (pd.Timestamp.today() - pd.to_datetime(overdue_df["DUEDATE"])).dt.days
            summary = overdue_df.groupby("CUSTOMERNAME").agg(
                Total_Overdue_Amount=("INVOICEAMOUNT", "sum"),
                Overdue_Invoices=("INVOICEID", "count"),
                Avg_Days_Late=("DAYS_PAST_DUE", "mean")
            ).sort_values("Total_Overdue_Amount", ascending=False).reset_index()

            st.metric("🔢 Overdue Customers", len(summary))
            st.dataframe(summary)
            st.subheader("📊 Overdue Amount by Customer")
            st.bar_chart(summary.set_index("CUSTOMERNAME")["Total_Overdue_Amount"])

# ---------- AGED RECEIVABLES ----------
with tab5:
    st.subheader("📆 Aged Receivables per Customer")
    if 'ar_df' in locals():
        ar_df["DAYS_PAST_DUE"] = (pd.Timestamp.today() - pd.to_datetime(ar_df["DUEDATE"])).dt.days.clip(lower=0)

        def aging_bucket(days):
            if days == 0:
                return "Not Due"
            elif days <= 30:
                return "1–30"
            elif days <= 60:
                return "31–60"
            elif days <= 90:
                return "61–90"
            else:
                return "90+"

        ar_df["AGING"] = ar_df["DAYS_PAST_DUE"].apply(aging_bucket)

        pivot = pd.pivot_table(ar_df, index="CUSTOMERNAME", columns="AGING", values="INVOICEAMOUNT", aggfunc="sum", fill_value=0)
        st.dataframe(pivot)

# ---------- FORECASTED IMPACT ----------
with tab6:
    st.subheader("📉 Forecasted Impact of Overdue Invoices")

    if 'ar_df' in locals():
        ar_df["InvoiceMonth"] = pd.to_datetime(ar_df["INVOICEDATE"]).dt.to_period("M").dt.to_timestamp()
        trend = ar_df[ar_df["STATUS"] != "Paid"].groupby("InvoiceMonth")["INVOICEAMOUNT"].sum().reset_index()

        chart = alt.Chart(trend).mark_line(point=True).encode(
            x="InvoiceMonth:T",
            y="INVOICEAMOUNT:Q",
            tooltip=["InvoiceMonth:T", "INVOICEAMOUNT"]
        ).properties(title="Overdue Invoice Trend", height=300)

        st.altair_chart(chart, use_container_width=True)

        if len(trend) >= 3:
            forecast = trend.tail(3)["INVOICEAMOUNT"].mean()
            st.metric("📈 Forecasted Next Month", f"${forecast:,.2f}")

# ---------- TOP VENDORS ----------
with tab7:
    st.subheader("🏆 Top Vendors by Payables")
    if 'ap_df' in locals():
        unpaid = ap_df[ap_df["STATUS"].isin(["Unpaid", "Partially Paid"])].copy()
        if not unpaid.empty:
            unpaid["DAYS_PAST_DUE"] = (pd.Timestamp.today() - pd.to_datetime(unpaid["DUEDATE"])).dt.days
            vendor_summary = unpaid.groupby("VENDORNAME").agg(
                Total_Outstanding=("INVOICEAMOUNT", "sum"),
                Invoices=("INVOICEID", "count"),
                Avg_Days_Past_Due=("DAYS_PAST_DUE", "mean")
            ).sort_values("Total_Outstanding", ascending=False).reset_index()
            st.dataframe(vendor_summary)
            st.bar_chart(vendor_summary.set_index("VENDORNAME")["Total_Outstanding"])
        else:
            st.info("✅ No unpaid vendor invoices.")

# ---------- DSO / DPO ----------
with tab8:
    st.subheader("📆 DSO / DPO Analysis")
    total_ap = ap_df["INVOICEAMOUNT"].sum()
    days = 30
    dso = round((outstanding_ar / total_ar) * days, 1) if total_ar else 0
    dpo = round((outstanding_ap / total_ap) * days, 1) if total_ap else 0

    c1, c2 = st.columns(2)
    c1.metric("📈 DSO", f"{dso} days")
    c2.metric("📉 DPO", f"{dpo} days")
