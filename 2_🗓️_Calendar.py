import streamlit as st
from streamlit_calendar import calendar
from utils import apply_global_styles, build_sidebar, get_tasks, get_era_theme_config # Correct import

st.set_page_config(page_title="TaskFlow Calendar", page_icon="🗓️", layout="wide")
apply_global_styles(); build_sidebar()
if not st.session_state.get("login_state"):
    st.switch_page("taskflow_app.py")

# --- Get the full, correct theme dictionary ---
current_theme = get_era_theme_config(st.session_state.get("era_mode", "Folklore"))

# --- Inject CSS using the correct theme data ---
st.markdown(f"""
<style>
    .fc-toolbar-title {{ color: {current_theme['text']} !important; }}
    .fc-daygrid-day {{ background-color: {current_theme['cal_bg']} !important; }}
    .fc-day-today {{ background-color: {current_theme['bg']} !important; border: 2px solid {current_theme['btn_bg']} !important; }}
    .fc-col-header-cell, .fc-daygrid-day-number {{ color: {current_theme['text']} !important; }}
    .fc-button, .fc-button-primary {{ 
        background-color: {current_theme['btn_bg']} !important;
        color: {current_theme['btn_text']} !important;
        border: none !important;
        background-image: none !important;
    }}
    .fc-button-primary:hover {{ background-color: {current_theme['btn_hover']} !important; }}
    .fc-button-active {{ background-color: {current_theme['btn_hover']} !important; }}
</style>
""", unsafe_allow_html=True)

# --- Display the themed title ---
st.markdown(f"<h1 class='themed-title'>🗓️ Task Calendar</h1>", unsafe_allow_html=True)
st.markdown("View all your tasks and their due dates in one place.")

username = st.session_state.get("user", "")
all_tasks = get_tasks(username)
calendar_events = []
for task in all_tasks:
    priority_colors = {
        "High": {"bg": "#ef5350", "border": "#d32f2f", "text": "#ffffff"},
        "Medium": {"bg": "#ffca28", "border": "#ffb300", "text": "#424242"},
        "Low": {"bg": "#66bb6a", "border": "#43a047", "text": "#ffffff"}
    }
    colors = priority_colors.get(task.get('priority', 'Medium'))
    calendar_events.append({
        "title": f"📌 {task['title']}", "start": task['due_date'], "end": task['due_date'],
        "backgroundColor": colors['bg'], "borderColor": colors['border'], "textColor": colors['text'],
        "allDay": True,
    })

calendar_options = {"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth,timeGridWeek,timeGridDay"}}
calendar(events=calendar_events, options=calendar_options)
