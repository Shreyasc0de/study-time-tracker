import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import hashlib

# Connect to SQLite
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# Create table for study logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS study_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    date TEXT,
    subject TEXT,
    hours REAL,
    tag TEXT,
    note TEXT
)
""")

# Create table for user credentials
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(input_password, stored_hash):
    return hash_password(input_password) == stored_hash

st.title("📚 Study Time Tracker - User Login")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    auth_mode = st.selectbox("Choose mode", ["Login", "Register"])

    if auth_mode == "Register":
        new_user = st.text_input("Create username")
        new_pass = st.text_input("Create password", type="password")
        if st.button("Register"):
            if new_user and new_pass:
                try:
                    cursor.execute(
                        "INSERT INTO users (username, password) VALUES (?, ?)",
                        (new_user, hash_password(new_pass))
                    )
                    conn.commit()
                    st.success("Account created! Please log in.")
                    st.stop()
                except sqlite3.IntegrityError:
                    st.error("Username already exists.")
            else:
                st.warning("Please fill out both fields.")
        st.stop()  # ✅ ← Make sure this is here too!

    elif auth_mode == "Login":
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        if st.button("Login"):
            cursor.execute("SELECT password FROM users WHERE username = ?", (username_input,))
            result = cursor.fetchone()
            if result and verify_password(password_input, result[0]):
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.success(f"Welcome, {username_input}!")
                st.rerun()

            else:
                st.error("Invalid credentials.")
        st.stop()  # ✅ stop showing dashboard if not logged in


username = st.session_state.username
st.sidebar.success(f"Logged in as {username}")

# === APP UI AFTER LOGIN ===

def load_user_data(username):
    query = "SELECT * FROM study_logs WHERE username = ?"
    return pd.read_sql(query, conn, params=(username,))

def add_study_entry(username, date, subject, hours, tag, note):
    cursor.execute(
        "INSERT INTO study_logs (username, date, subject, hours, tag, note) VALUES (?, ?, ?, ?, ?, ?)",
        (username, date, subject, hours, tag, note)
    )
    conn.commit()

# === Study Entry Form ===
st.subheader("➕ Add Study Session")

with st.form("entry_form"):
    date = st.date_input("Date")
    subject = st.selectbox("Subject", ["Math", "Science", "History", "English", "Other"])
    hours = st.number_input("Hours Spent", min_value=0.0, format="%.2f")
    tag = st.selectbox("Tag", ["Exam Prep", "Reading", "Homework", "Other"])
    note = st.text_input("Optional Note")
    submitted = st.form_submit_button("Add Entry")

    if submitted:
        add_study_entry(username, date, subject, hours, tag, note)
        st.success("Entry added successfully!")

# === Load User's Data ===
df = load_user_data(username)
df["date"] = pd.to_datetime(df["date"])

# === Weekly Progress Tracker ===
st.subheader("🎯 Weekly Goal Tracker")
weekly_goal = st.number_input("Set your weekly goal (hours)", min_value=1.0, step=1.0, value=10.0)

today = datetime.today().date()
start_of_week = today - timedelta(days=today.weekday())
this_week = df[df["date"].dt.date >= start_of_week]
weekly_total = this_week["hours"].sum()

st.write(f"Hours studied this week: **{weekly_total:.2f} / {weekly_goal:.2f}**")
st.progress(min(weekly_total / weekly_goal, 1.0))

# === Daily Chart ===
st.subheader("📅 Daily Study Breakdown (This Week)")
if not this_week.empty:
    daily_hours = this_week.groupby("date")["hours"].sum()
    st.bar_chart(daily_hours)

  # Create user credentials table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")
conn.commit()
  

# === Full Log Table ===
st.subheader("📋 Your Study Log")
st.dataframe(df)

st.markdown("### ✏️ Edit or Delete Entries")

if not df.empty:
    selected_id = st.selectbox("Select an entry to modify", df["id"])
    entry = df[df["id"] == selected_id].iloc[0]

    with st.form("edit_form"):
        edit_date = st.date_input("Edit Date", value=pd.to_datetime(entry["date"]))
        edit_subject = st.selectbox("Edit Subject", ["Math", "Science", "History", "English", "Other"], index=["Math", "Science", "History", "English", "Other"].index(entry["subject"]))
        edit_hours = st.number_input("Edit Hours", min_value=0.0, value=float(entry["hours"]))
        edit_tag = st.selectbox("Edit Tag", ["Exam Prep", "Reading", "Homework", "Other"], index=["Exam Prep", "Reading", "Homework", "Other"].index(entry["tag"]))
        edit_note = st.text_input("Edit Note", value=entry["note"])

        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Update Entry"):
                cursor.execute("""
                    UPDATE study_logs SET date = ?, subject = ?, hours = ?, tag = ?, note = ?
                    WHERE id = ? AND username = ?
                """, (edit_date, edit_subject, edit_hours, edit_tag, edit_note, selected_id, username))
                conn.commit()
                st.success("Entry updated successfully!")
                st.rerun()

        with col2:
            if st.form_submit_button("Delete Entry"):
                cursor.execute("DELETE FROM study_logs WHERE id = ? AND username = ?", (selected_id, username))
                conn.commit()
                st.warning("Entry deleted.")
                st.rerun()



