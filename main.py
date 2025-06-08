# main.py
import streamlit as st
from snowflake_connector import run_query
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt


# Set config first!
st.set_page_config(page_title="AR/AP Dashboard", layout="wide")
st.title("📊 Accounts Receivable / Payable Dashboard")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📥 Accounts Receivable", "📤 Accounts Payable", "📚 Combined Summary", "🚨 Top Overdue Customers", "📆 Aged Receivables", "📉 Forecasted Impact", "📦 Top Vendors", "📆 DSO / DPO Analysis"])

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


# ---------- TOP OVERDUE CUSTOMERS ----------
with tab4:
    st.subheader("🚨 Top Overdue Customers")
    overdue_df = ar_df.copy()

    # Only unpaid invoices past due date
    overdue_df = overdue_df[
        (overdue_df["STATUS"] != "Paid") &
        (pd.to_datetime(overdue_df["DUEDATE"]) < pd.Timestamp.today())
    ].copy()

    if overdue_df.empty:
        st.info("✅ No overdue invoices found.")
    else:
        overdue_df["DAYS_PAST_DUE"] = (pd.Timestamp.today() - pd.to_datetime(overdue_df["DUEDATE"])).dt.days

        summary = (
            overdue_df.groupby("CUSTOMERNAME")
            .agg(
                Total_Overdue_Amount=("INVOICEAMOUNT", "sum"),
                Overdue_Invoices=("INVOICEID", "count"),
                Average_Days_Late=("DAYS_PAST_DUE", "mean")
            )
            .sort_values(by="Total_Overdue_Amount", ascending=False)
            .reset_index()
        )

        st.metric("🔢 Number of Overdue Customers", len(summary))
        st.dataframe(summary)

        # Optional: Bar chart
        st.subheader("📊 Overdue Amount by Customer")
        st.bar_chart(summary.set_index("CUSTOMERNAME")["Total_Overdue_Amount"])


# ---------- AGED RECEIVABLES PER CUSTOMER ----------
with tab5:
    st.subheader("📆 Aged Receivables per Customer")

    aging_df = ar_df.copy()
    aging_df["DAYS_PAST_DUE"] = (pd.Timestamp.today() - pd.to_datetime(aging_df["DUEDATE"])).dt.days
    aging_df["DAYS_PAST_DUE"] = aging_df["DAYS_PAST_DUE"].apply(lambda x: max(0, x))  # no negatives

    def aging_bucket(days):
        if days <= 0:
            return "Not Due"
        elif days <= 30:
            return "1–30 Days"
        elif days <= 60:
            return "31–60 Days"
        elif days <= 90:
            return "61–90 Days"
        else:
            return "90+ Days"

    aging_df["AgingBucket"] = aging_df["DAYS_PAST_DUE"].apply(aging_bucket)

    # Pivot for customer vs. aging bucket
    pivot = pd.pivot_table(
        aging_df,
        index="CUSTOMERNAME",
        columns="AgingBucket",
        values="INVOICEAMOUNT",
        aggfunc="sum",
        fill_value=0,
        margins=True,
        margins_name="Total"
    ).reset_index()

    st.dataframe(pivot)


# ---------- Forecasting Impact of Unpaid Invoices ----------
with tab6:
    st.subheader("📉 Forecasted Impact of Overdue Invoices")

    # Group overdue amount by month
    forecast_df = ar_df.copy()
    forecast_df["InvoiceMonth"] = pd.to_datetime(forecast_df["INVOICEDATE"]).dt.to_period("M").dt.to_timestamp()

    monthly_trend = (
        forecast_df[forecast_df["STATUS"] != "Paid"]
        .groupby("InvoiceMonth")["INVOICEAMOUNT"]
        .sum()
        .reset_index()
    )

    # Visualization
    chart = alt.Chart(monthly_trend).mark_line(point=True).encode(
        x="InvoiceMonth:T",
        y="INVOICEAMOUNT:Q",
        tooltip=["InvoiceMonth:T", "INVOICEAMOUNT"]
    ).properties(
        title="Overdue Invoices Trend",
        width=700
    )

    st.altair_chart(chart)

    # Optional: Show last 3-month average and project next month
    if len(monthly_trend) >= 3:
        avg = monthly_trend.tail(3)["INVOICEAMOUNT"].mean()
        st.metric("📈 Forecasted Overdue Next Month", f"${avg:,.2f}")


# ---------- TOP VENDORS (BY PAYABLE AMOUNT) ----------
with tab7:
    st.subheader("🏆 Top Vendors by Payables")

    # Ensure AP data is loaded
    ap_df = run_query("SELECT * FROM AP_INVOICES")

    if isinstance(ap_df, pd.DataFrame) and not ap_df.empty:
        ap_df.columns = ap_df.columns.str.upper()

        # Filter unpaid or partially paid invoices
        unpaid_df = ap_df[ap_df["STATUS"].isin(["Unpaid", "Partially Paid"])].copy()

        if unpaid_df.empty:
            st.info("✅ No outstanding vendor payments.")
        else:
            unpaid_df["DAYS_PAST_DUE"] = (pd.Timestamp.today() - pd.to_datetime(unpaid_df["DUEDATE"])).dt.days

            summary = (
                unpaid_df.groupby("VENDORNAME")
                .agg(
                    Total_Outstanding_Amount=("INVOICEAMOUNT", "sum"),
                    Outstanding_Invoices=("INVOICEID", "count"),
                    Avg_Days_Past_Due=("DAYS_PAST_DUE", "mean")
                )
                .sort_values(by="Total_Outstanding_Amount", ascending=False)
                .reset_index()
            )

            st.metric("🔢 Number of Vendors with Outstanding AP", len(summary))
            st.dataframe(summary)

            # Chart
            st.subheader("📊 Outstanding Payables by Vendor")
            st.bar_chart(summary.set_index("VENDORNAME")["Total_Outstanding_Amount"])
    else:
        st.warning("No AP data available.")

# ---------- DSO/DPO ----------
with tab8:
    st.subheader("DSO & DPO Metrics")

    # Time Period - last 30 days (can customize)
    period_days = 30

    # DSO Calculation
    try:
        ar_total_sales = ar_df["INVOICEAMOUNT"].sum()
        ar_outstanding = ar_df[ar_df["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum()
        dso = round((ar_outstanding / ar_total_sales) * period_days, 2) if ar_total_sales else 0
    except Exception as e:
        st.error(f"Error calculating DSO: {e}")
        dso = 0

    # DPO Calculation
    try:
        ap_total_purchases = ap_df["INVOICEAMOUNT"].sum()
        ap_outstanding = ap_df[ap_df["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum()
        dpo = round((ap_outstanding / ap_total_purchases) * period_days, 2) if ap_total_purchases else 0
    except Exception as e:
        st.error(f"Error calculating DPO: {e}")
        dpo = 0

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📈 Days Sales Outstanding (DSO)", f"{dso} days")
        st.caption("How long it takes to collect payments from customers.")

    with col2:
        st.metric("📉 Days Payable Outstanding (DPO)", f"{dpo} days")
        st.caption("How long it takes to pay suppliers.")

    
    st.subheader("📈 DSO / DPO Trends Over Time")

    # Convert date columns if needed
    ar_df["INVOICEDATE"] = pd.to_datetime(ar_df["INVOICEDATE"])
    ap_df["INVOICEDATE"] = pd.to_datetime(ap_df["INVOICEDATE"])

    # Group by month
    ar_df["InvoiceMonth"] = ar_df["INVOICEDATE"].dt.to_period("M").dt.to_timestamp()
    ap_df["InvoiceMonth"] = ap_df["INVOICEDATE"].dt.to_period("M").dt.to_timestamp()

    # DSO trend
    ar_trend = ar_df.groupby("InvoiceMonth").apply(
        lambda x: round((x[x["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum() / x["INVOICEAMOUNT"].sum()) * 30, 2)
    ).reset_index(name="DSO")

    # DPO trend
    ap_trend = ap_df.groupby("InvoiceMonth").apply(
        lambda x: round((x[x["STATUS"] != "Paid"]["INVOICEAMOUNT"].sum() / x["INVOICEAMOUNT"].sum()) * 30, 2)
    ).reset_index(name="DPO")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(ar_trend["InvoiceMonth"], ar_trend["DSO"], label="DSO", marker="o", color="tab:blue")
    ax.plot(ap_trend["InvoiceMonth"], ap_trend["DPO"], label="DPO", marker="s", color="tab:orange")

    ax.set_title("DSO / DPO Trend Over Time")
    ax.set_xlabel("Month")
    ax.set_ylabel("Days")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)
