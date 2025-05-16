
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import json



# Load or initialize data
def load_data():
    
    if os.path.exists("study_log.csv"):
        return pd.read_csv("study_log.csv")
    else:
        return pd.DataFrame(columns=["Date", "Subject", "Hours", "Tag", "Note"])
    

def save_data(df):
    df.to_csv("study_log.csv", index=False)

import json  # Make sure this is at the top with other imports

STREAK_FILE = "streak.json"

def update_goal_streak(week_total, goal):
    today = datetime.today().date()
    week_id = today.strftime("%Y-%W")  # Year-week format like '2025-20'

    if os.path.exists(STREAK_FILE):
        with open(STREAK_FILE, "r") as f:
            streak_data = json.load(f)
    else:
        streak_data = {"streak": 0, "last_week": "", "weeks": {}}

    if week_id not in streak_data["weeks"]:
        if week_total >= goal:
            streak_data["streak"] += 1
        else:
            streak_data["streak"] = 0  # reset
        streak_data["weeks"][week_id] = week_total
        streak_data["last_week"] = week_id

        with open(STREAK_FILE, "w") as f:
            json.dump(streak_data, f)

    return streak_data["streak"]



GOAL_FILE = "weekly_goal.json"

def load_weekly_goal():
    if os.path.exists(GOAL_FILE):
        with open(GOAL_FILE, "r") as f:
            return json.load(f).get("goal", 10.0)
    return 10.0

def save_weekly_goal(goal):
    with open(GOAL_FILE, "w") as f:
        json.dump({"goal": goal}, f)



# App title
st.title("📚 Study Time Tracker")

df= load_data()
# Weekly Goal Tracker
st.subheader("🎯 Weekly Goal Tracker")
saved_goal = load_weekly_goal()
weekly_goal = st.number_input("Set your weekly goal (in hours)", min_value=1.0, step=1.0, value=saved_goal, key="goal_input")

if weekly_goal != saved_goal:
    save_weekly_goal(weekly_goal)


# Filter this week's data
today = datetime.today().date()
start_of_week = today - timedelta(days=today.weekday())  # Monday
df["Date"] = pd.to_datetime(df["Date"]).dt.date
this_week = df[df["Date"] >= start_of_week]

# Sum hours
weekly_total = this_week["Hours"].sum()

streak = update_goal_streak(weekly_total, weekly_goal)
st.success(f"🔥 Weekly Streak: {streak} week(s) in a row hitting your goal!")

# Progress display
st.write(f"Hours studied this week: **{weekly_total:.2f} / {weekly_goal:.2f}**")
progress = min(weekly_total / weekly_goal, 1.0)
st.progress(progress)


# Input form
with st.form("entry_form"):
    date = st.date_input("Date")
    subject = st.selectbox("Subject", ["Math", "Science", "History", "English", "Other"])
    hours = st.number_input("Hours Spent", min_value=0.0, format="%.2f")
    tag = st.selectbox("Tag", ["Exam Prep", "Reading", "Homework", "Other"])
    note = st.text_input("Optional Note")

    submitted = st.form_submit_button("Add Entry")
    if submitted:
        df = load_data()
        new_entry = {"Date": date, "Subject": subject, "Hours": hours, "Tag": tag, "Note": note}
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        save_data(df)
        st.success("Entry added successfully!")

st.subheader("📅 Daily Study Breakdown (This Week)")
if not this_week.empty:
    daily_hours = this_week.groupby("Date")["Hours"].sum()
    st.bar_chart(daily_hours)
else:
    st.info("No study sessions logged this week yet.")


# Display data
df = load_data()
st.subheader("📈 Hours Studied by Subject")
if not df.empty:
    chart_data = df.groupby("Subject")["Hours"].sum()
    st.bar_chart(chart_data)

st.subheader("🗂️ Session Log")
st.dataframe(df)
