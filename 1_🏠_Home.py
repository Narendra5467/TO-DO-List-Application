import streamlit as st
from datetime import date
import pandas as pd
from utils import (
    apply_global_styles, build_sidebar, add_task, get_tasks,
    update_task_status, delete_task, update_task_details, update_task, DEFAULT_TAGS
)

st.set_page_config(page_title="TaskFlow Home", page_icon="🏠", layout="wide")
apply_global_styles(); build_sidebar()
if not st.session_state.get("login_state"):
    st.switch_page("taskflow_app.py")

username = st.session_state.user
era_banner_path = f"images/{st.session_state.era_mode}.png"
st.image(era_banner_path, use_container_width=True)

st.title("📝 Your Tasks")
with st.expander("➕ Add New Task", expanded=False):
    with st.form("new_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        title = col1.text_input("Task Description")
        priority = col1.selectbox("Priority", ["High", "Medium", "Low"])
        due_date = col2.date_input("Due Date", min_value=date.today())
        tags = col2.text_input("Tags (comma-separated)", placeholder="work, urgent")
        if st.form_submit_button("Add Task", use_container_width=True):
            if title:
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
                add_task(username, title, priority, due_date.isoformat(), tag_list)
                st.rerun()
st.markdown("---")
all_tasks = get_tasks(username)
st.subheader("Filter & Search")
f1, f2, f3, f4 = st.columns(4)
filter_status = f1.selectbox("Filter by Status", ["All", "Pending", "Completed"])
all_tags = sorted(list(set(tag for task in all_tasks for tag in task.get("tags", []))))
filter_tag = f2.selectbox("Filter by Tag", ["All"] + all_tags)
search = f3.text_input("Search", placeholder="Title or tag")
sort_order = f4.selectbox("Sort Priority", ["High to Low", "Low to High"])

tasks_to_display = all_tasks
if filter_status != "All": tasks_to_display = [t for t in tasks_to_display if t.get("status") == filter_status]
if filter_tag != "All": tasks_to_display = [t for t in tasks_to_display if filter_tag in t.get("tags", [])]
if search:
    search_term = search.lower()
    tasks_to_display = [t for t in tasks_to_display if search_term in t.get("title", "").lower() or search_term in " ".join(t.get("tags", [])).lower()]
pending_tasks = [t for t in tasks_to_display if t.get("status") != 'Completed']
completed_tasks = [t for t in tasks_to_display if t.get("status") == 'Completed']

priority_map = {"High": 0, "Medium": 1, "Low": 2}
should_reverse_sort = (sort_order == "Low to High")
pending_tasks.sort(key=lambda x: priority_map.get(x['priority'], 1), reverse=should_reverse_sort)

st.subheader("Pending Tasks")
if not pending_tasks:
    st.info("No pending tasks match your filters. Great job! 🎉")
else:
    for task in pending_tasks:
        task_id = str(task["_id"])
        with st.container():
            st.markdown(f'<div class="task-card">', unsafe_allow_html=True)
            col_check, col_details, col_actions = st.columns([1, 10, 2])
            col_check.checkbox("Done", key=f"check_{task_id}", value=False, on_change=update_task_status, args=(task_id, "Completed"))
            with col_details:
                priority_icon = "🔴" if task['priority'] == 'High' else "🟠" if task['priority'] == 'Medium' else "🟢"
                tags_html = " ".join([f'<span class="tag" style="background-color: #eee; color: #333; padding: 2px 6px; border-radius: 5px; font-size: 0.8em;">{tag}</span>' for tag in task.get("tags", [])])
                st.markdown(f"**{task['title']}**<br><small>📅 {task['due_date']} | {priority_icon} {task['priority']} | {tags_html}</small>", unsafe_allow_html=True)
            with col_actions:
                edit_col, delete_col = st.columns(2)
                if edit_col.button("✏️", key=f"edit_{task_id}", help="Edit Task"):
                    st.session_state.editing_task_id = task_id
                    st.rerun()
                if delete_col.button("🗑️", key=f"del_{task_id}", help="Delete Task"):
                    delete_task(task_id)
                    st.rerun()
            if st.session_state.get("editing_task_id") == task_id:
                with st.expander("Edit Task", expanded=True):
                    with st.form(key=f"edit_form_{task_id}"):
                        new_title = st.text_input("Title", value=task.get("title", ""), key=f"title_{task_id}")
                        new_status = st.selectbox("Status", ["Pending", "In Progress", "Completed"], index=["Pending", "In Progress", "Completed"].index(task.get("status", "Pending")), key=f"status_{task_id}")
                        new_priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(task.get("priority", "Medium")), key=f"priority_{task_id}")
                        new_due_date = st.date_input("Due Date", value=date.fromisoformat(task.get("due_date", date.today().isoformat())), key=f"due_{task_id}")
                        task_tags = task.get("tags", [])
                        tag_options = sorted(list(set(DEFAULT_TAGS + list(st.session_state.get("tags", []))) | set(task_tags)))
                        new_tags = st.multiselect("Tags", options=tag_options, default=task_tags, key=f"tags_{task_id}")
                        save_col, cancel_col = st.columns(2)
                        if save_col.form_submit_button("Save Changes", use_container_width=True):
                            update_task(task_id, new_title=new_title, new_priority=new_priority, new_due_date=new_due_date.isoformat(), new_tags=new_tags, new_status=new_status)
                            del st.session_state.editing_task_id
                            st.rerun()
                        if cancel_col.form_submit_button("Cancel", use_container_width=True):
                            del st.session_state.editing_task_id
                            st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

if completed_tasks:
    with st.expander(f"✅ Completed Tasks ({len(completed_tasks)})"):
        for task in completed_tasks:
            task_id = str(task["_id"])
            col_undo, col_details, col_delete = st.columns([1, 10, 1])
            with col_undo:
                if st.button("↩️", key=f"undo_{task_id}", help="Mark as Pending"):
                    update_task_status(task_id, "Pending")
                    st.rerun()
            with col_details:
                st.markdown(f"~~_{task['title']}_~~")
            with col_delete:
                if st.button("🗑️", key=f"del_comp_{task_id}", help="Delete Task Permanently"):
                    delete_task(task_id)
                    st.rerun()
