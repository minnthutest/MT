import io
import datetime
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from logic.expense_manager import (
    register_user, authenticate_user, update_user_password,
    set_user_budget, get_user_budget, add_expense, get_expenses,
    filter_expenses_by_category, get_total_by_month, get_total_by_year,
    get_category_summary, get_monthly_summary, delete_expense, update_expense
)
from database.database import create_user_table, create_expense_table, delete_user, DATABASE_URL

# -------------------- Database --------------------
create_user_table()
create_expense_table()

# -------------------- Page --------------------
st.set_page_config(page_title="Expense Tracker", page_icon="💸", layout="wide")

def load_css():
    css_path = Path(__file__).parent / "css" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

load_css()

# -------------------- Session --------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# -------------------- Authentication --------------------
if not st.session_state.logged_in:
    auth_mode = st.sidebar.selectbox(
        "Account",
        ["Login", "Register", "Forgot Password"]
    )

    if auth_mode == "Register":
        st.title("💸 Expense Tracker")
        st.subheader("Create Account")

        with st.form("register_form"):
            name = st.text_input("Name")
            email = st.text_input("Email")
            password = st.text_input("Password (6-digit number)", type="password", max_chars=6)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            secret = st.text_input("Secret Word (for password recovery)", type="password")
            submitted = st.form_submit_button("Register")

        if submitted:
            if not name.strip():
                st.error("Please enter your name.")
            elif len(password) != 6 or not password.isdigit():
                st.error("Password must be exactly 6 digits.")
            elif "@" not in email or "." not in email.split("@")[-1]:
                st.error("Please enter a valid email address.")
            elif not secret.strip():
                st.error("Please enter a secret word.")
            else:
                try:
                    register_user(name.strip(), email.strip().lower(), password, gender, secret.strip())
                    st.success("✅ Registration successful. You can now login.")
                except ValueError as e:
                    st.error(f"❌ {e}")

    elif auth_mode == "Login":
        st.title("💸 Expense Tracker")
        st.subheader("Login")

        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password", max_chars=6)
            submitted = st.form_submit_button("Login")

        if submitted:
            user = authenticate_user(email.strip().lower(), password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("❌ Invalid email or password.")

    else:
        st.title("🔐 Password Recovery")
        with st.form("reset_form"):
            email = st.text_input("Registered email")
            secret = st.text_input("Secret word", type="password")
            new_password = st.text_input("New password (6-digit number)", type="password", max_chars=6)
            submitted = st.form_submit_button("Reset Password")

        if submitted:
            if len(new_password) != 6 or not new_password.isdigit():
                st.error("Password must be exactly 6 digits.")
            elif update_user_password(email.strip().lower(), secret.strip(), new_password):
                st.success("✅ Password reset successful. You can now login.")
            else:
                st.error("❌ Incorrect email or secret word.")

    st.info("🔒 Your data is stored in a persistent SQL database. Local data is kept in the project's `data/expenses.db` file.")
    st.stop()

# -------------------- Logged-in area --------------------
user = st.session_state.user
user_id = user[0]
user_name = user[1]
user_email = user[2]

st.sidebar.success(f"Logged in as: {user_name}")
auth_action = st.sidebar.selectbox("Account", ["My Account", "Logout", "Delete Account"])

if auth_action == "Logout":
    if st.sidebar.button("Confirm Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
    st.stop()

if auth_action == "Delete Account":
    st.subheader("⚠️ Delete Account")
    st.warning("This permanently deletes your account and all expenses belonging to it.")
    secret = st.text_input("Enter your secret word", type="password")
    if st.button("Delete My Account", type="primary"):
        if delete_user(user_id, secret.strip()):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.success("Account deleted successfully.")
            st.rerun()
        else:
            st.error("Incorrect secret word.")
    st.stop()

if auth_action == "My Account":
    st.sidebar.caption(f"Email: {user_email}")

# -------------------- Main --------------------
st.title(f"💸 {user_name}'s Expense Tracker")

menu = st.sidebar.radio("Menu", ["Dashboard", "Add Expense", "View Expenses", "Charts"])

if menu == "Dashboard":
    st.subheader("📊 Dashboard")

    total_year = get_total_by_year(user_id, datetime.date.today().year)
    total_month = get_total_by_month(user_id, datetime.date.today().month, datetime.date.today().year)
    budget = get_user_budget(user_id)

    c1, c2, c3 = st.columns(3)
    c1.metric("This Month", f"{total_month:,.0f} MMK")
    c2.metric("This Year", f"{total_year:,.0f} MMK")
    c3.metric("Monthly Budget", f"{budget:,.0f} MMK")

    st.markdown("### 💰 Monthly Budget")
    with st.form("budget_form"):
        new_budget = st.number_input("Budget limit (MMK)", min_value=0.0, value=float(budget), step=1000.0)
        save_budget = st.form_submit_button("Save Budget")
    if save_budget:
        set_user_budget(user_id, new_budget)
        st.success("Budget saved.")
        st.rerun()

    if budget > 0:
        remaining = budget - total_month
        if remaining >= 0:
            st.info(f"Remaining this month: **{remaining:,.0f} MMK**")
        else:
            st.error(f"Budget exceeded by **{abs(remaining):,.0f} MMK**")

elif menu == "Add Expense":
    st.subheader("➕ Add New Expense")
    with st.form("expense_form", clear_on_submit=True):
        date = st.date_input("Date", value=datetime.date.today())
        category = st.selectbox("Category", ["Food", "Transport", "Bills", "Others"])
        amount = st.number_input("Amount (MMK)", min_value=0.0, format="%.2f")
        description = st.text_input("Description")
        submitted = st.form_submit_button("Add Expense", type="primary")
        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than 0.")
            else:
                add_expense(user_id, date, category, amount, description)
                st.success("✅ Expense added successfully.")

elif menu == "View Expenses":
    st.subheader("📋 Expenses")

    category_filter = st.selectbox("Filter by Category", ["All", "Food", "Transport", "Bills", "Others"])
    data = get_expenses(user_id) if category_filter == "All" else filter_expenses_by_category(user_id, category_filter)

    df = pd.DataFrame(data, columns=["ID", "Date", "Category", "Amount", "Description"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    if not df.empty:
        st.markdown("### ✏️ Edit / 🗑️ Delete")
        selected_id = st.selectbox("Select Expense ID", df["ID"].astype(str))
        selected_row = df[df["ID"] == int(selected_id)].iloc[0]
        action = st.radio("Action", ["Edit", "Delete"], horizontal=True)

        if action == "Edit":
            categories = ["Food", "Transport", "Bills", "Others"]
            with st.form("edit_form"):
                new_date = st.date_input("Date", pd.to_datetime(selected_row["Date"]).date())
                new_category = st.selectbox("Category", categories, index=categories.index(selected_row["Category"]))
                new_amount = st.number_input("Amount (MMK)", min_value=0.0, value=float(selected_row["Amount"]), format="%.2f")
                new_description = st.text_input("Description", value=str(selected_row["Description"] or ""))
                submit_edit = st.form_submit_button("Update Expense", type="primary")
            if submit_edit:
                if new_amount <= 0:
                    st.error("Amount must be greater than 0.")
                else:
                    update_expense(int(selected_id), user_id, new_date, new_category, new_amount, new_description)
                    st.success("✅ Expense updated.")
                    st.rerun()

        else:
            if st.button("Confirm Delete", type="primary"):
                if delete_expense(int(selected_id), user_id):
                    st.success("🗑️ Expense deleted.")
                    st.rerun()

    st.markdown("### 📆 Total Overview")
    c1, c2 = st.columns(2)
    with c1:
        selected_month = st.selectbox(
            "Month", range(1, 13),
            format_func=lambda x: datetime.date(1900, x, 1).strftime("%B")
        )
        selected_year_for_month = st.selectbox("Month Year", range(datetime.date.today().year - 5, datetime.date.today().year + 2))
        total_month = get_total_by_month(user_id, selected_month, selected_year_for_month)
        st.metric("Monthly Total", f"{total_month:,.0f} MMK")
    with c2:
        selected_year = st.selectbox("Year", range(2022, datetime.date.today().year + 2))
        total_year = get_total_by_year(user_id, selected_year)
        st.metric("Yearly Total", f"{total_year:,.0f} MMK")

elif menu == "Charts":
    st.subheader("📊 Expense Charts")

    category_summary = get_category_summary(user_id)
    if not category_summary.empty:
        pie_chart = px.pie(category_summary, names="Category", values="Total", title="Expenses by Category")
        st.plotly_chart(pie_chart, use_container_width=True)
        try:
            img_buf = io.BytesIO(pie_chart.to_image(format="png"))
            st.download_button("📥 Download Category Pie Chart", data=img_buf.getvalue(),
                               file_name="category_chart.png", mime="image/png")
        except Exception:
            st.info("PNG export requires a working Kaleido installation.")

    monthly_summary = get_monthly_summary(user_id)
    if not monthly_summary.empty:
        bar_chart = px.bar(monthly_summary, x="Month", y="Total", title="Monthly Expenses")
        st.plotly_chart(bar_chart, use_container_width=True)
        try:
            img_buf = io.BytesIO(bar_chart.to_image(format="png"))
            st.download_button("📥 Download Monthly Bar Chart", data=img_buf.getvalue(),
                               file_name="monthly_chart.png", mime="image/png")
        except Exception:
            st.info("PNG export requires a working Kaleido installation.")
