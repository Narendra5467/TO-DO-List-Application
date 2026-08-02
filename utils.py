import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import date, datetime, timedelta
import re
import json
import os
import uuid
from pymongo.errors import ConfigurationError, PyMongoError


DEFAULT_TAGS = ["Work", "Personal", "Urgent", "Shopping"]

# --- DB and User Functions with local JSON fallback ---
DATA_FILE = os.path.join(os.path.dirname(__file__), "taskflow_data.json")


def _read_data_file():
    if not os.path.exists(DATA_FILE):
        data = {"users": [], "tasks": []}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"users": [], "tasks": []}


def _write_data_file(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str, indent=2)


def _normalise_tags(tags):
    if not tags:
        return []
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    return sorted(list(dict.fromkeys([tag.strip() for tag in tags if str(tag).strip()])))


def get_mongo_uri():
    try:
        uri = st.secrets.get("mongo", {}).get("uri")
    except Exception:
        uri = None
    if uri:
        return uri
    return os.getenv("MONGO_URI")


@st.cache_resource
def get_mongo_client():
    MONGO_URI = get_mongo_uri()
    if not MONGO_URI:
        return None
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
        return client
    except (ConfigurationError, PyMongoError, Exception):
        return None


def get_db():
    client = get_mongo_client()
    if client:
        return client["taskflow_db"]
    return None


def get_tasks_collection():
    db = get_db()
    if db:
        return db["tasks"]
    return None


def get_users_collection():
    db = get_db()
    if db:
        return db["users"]
    return None

def create_user(username, password):
    if len(username) < 3:
        return "Username must be at least 3 characters long."
    if len(password) < 4:
        return "Password must be at least 4 characters long."
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return "Username can only contain letters, numbers, and underscores."

    users_col = get_users_collection()
    if users_col:
        if users_col.find_one({"username": username}):
            return "Username already exists."
        users_col.insert_one({"username": username, "password": password})
        return True

    data = _read_data_file()
    if any(u.get("username") == username for u in data.get("users", [])):
        return "Username already exists."
    data["users"].append({"username": username, "password": password})
    _write_data_file(data)
    return True


def authenticate_user(username, password):
    users_col = get_users_collection()
    if users_col:
        user_data = users_col.find_one({"username": username})
        if user_data and user_data.get("password") == password:
            return user_data
        return None

    data = _read_data_file()
    for u in data.get("users", []):
        if u.get("username") == username and u.get("password") == password:
            return u
    return None

@st.cache_data
def get_tasks(username: str):
    print(f"CACHE MISS: Fetching tasks for {username} from DB or local file.")
    tasks_col = get_tasks_collection()
    if tasks_col:
        return list(tasks_col.find({"username": username}))

    data = _read_data_file()
    return [t for t in data.get("tasks", []) if t.get("username") == username]


def _clear_tasks_cache():
    try:
        get_tasks.clear()
    except Exception:
        pass


def add_task(username: str, title: str, priority: str, due_date: str, tags: list, status: str = "Pending"):
    tags = _normalise_tags(tags)
    tasks_col = get_tasks_collection()
    if tasks_col:
        tasks_col.insert_one({"username": username, "title": title, "status": status, "priority": priority, "due_date": due_date, "tags": tags, "created_at": datetime.utcnow()})
        _clear_tasks_cache()
        return f"Task '{title}' was successfully added."

    data = _read_data_file()
    task_id = str(uuid.uuid4())
    new_task = {"_id": task_id, "username": username, "title": title, "status": status, "priority": priority, "due_date": due_date, "tags": tags, "created_at": datetime.utcnow().isoformat()}
    data.setdefault("tasks", []).append(new_task)
    _write_data_file(data)
    _clear_tasks_cache()
    return f"Task '{title}' was successfully added."


def update_task_status(task_id: str, new_status: str):
    tasks_col = get_tasks_collection()
    if tasks_col:
        tasks_col.update_one({"_id": ObjectId(task_id)}, {"$set": {"status": new_status}})
        _clear_tasks_cache()
        return

    data = _read_data_file()
    changed = False
    for t in data.get("tasks", []):
        if str(t.get("_id")) == str(task_id):
            t["status"] = new_status
            changed = True
            break
    if changed:
        _write_data_file(data)
        _clear_tasks_cache()


def delete_task(task_id: str):
    tasks_col = get_tasks_collection()
    if tasks_col:
        tasks_col.delete_one({"_id": ObjectId(task_id)})
        _clear_tasks_cache()
        return

    data = _read_data_file()
    data["tasks"] = [t for t in data.get("tasks", []) if str(t.get("_id")) != str(task_id)]
    _write_data_file(data)
    _clear_tasks_cache()


def update_task(task_id: str, new_title: str = None, new_priority: str = None, new_due_date: str = None, new_tags: list = None, new_status: str = None):
    tasks_col = get_tasks_collection()
    if tasks_col:
        update_data = {}
        if new_title:
            update_data["title"] = new_title
        if new_priority:
            update_data["priority"] = new_priority
        if new_due_date:
            update_data["due_date"] = new_due_date
        if new_tags is not None:
            update_data["tags"] = _normalise_tags(new_tags)
        if new_status:
            update_data["status"] = new_status
        if not update_data:
            return False
        tasks_col.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
        _clear_tasks_cache()
        return True

    data = _read_data_file()
    changed = False
    for t in data.get("tasks", []):
        if str(t.get("_id")) == str(task_id):
            if new_title:
                t["title"] = new_title
            if new_priority:
                t["priority"] = new_priority
            if new_due_date:
                t["due_date"] = new_due_date
            if new_tags is not None:
                t["tags"] = _normalise_tags(new_tags)
            if new_status:
                t["status"] = new_status
            changed = True
            break
    if changed:
        _write_data_file(data)
        _clear_tasks_cache()
        return True
    return False


def update_task_details(task_id: str, new_priority: str, new_due_date: str, new_tags: list):
    return update_task(task_id, new_priority=new_priority, new_due_date=new_due_date, new_tags=new_tags)


def update_task_by_title(username: str, title: str, new_status: str = None, new_priority: str = None, new_due_date: str = None, new_tags: list = None):
    tasks_col = get_tasks_collection(); query = {"username": username, "title": {"$regex": f"^{title}$", "$options": "i"}}; task_to_update = tasks_col.find_one(query)
    if not task_to_update: return f"Error: I couldn't find a task with the exact title '{title}'."
    update_data = {};
    if new_status: update_data["status"] = new_status
    if new_priority: update_data["priority"] = new_priority
    if new_due_date: update_data["due_date"] = new_due_date
    if new_tags is not None: updated_tags = sorted(list(set(task_to_update.get("tags", [])) | set(new_tags))); update_data["tags"] = updated_tags
    if not update_data: return "You didn't specify what to change."
    result = tasks_col.update_one(query, {"$set": update_data}); get_tasks.clear()
    if result.modified_count > 0: return f"Successfully updated the task: '{title}'."
    else: return f"The task '{title}' already had these properties. No update was necessary."

def delete_task_by_title(username: str, title: str, priority: str = None, tags: list = None):
    tasks_col = get_tasks_collection(); query = {"username": username, "title": {"$regex": title, "$options": "i"}}
    if priority: query["priority"] = priority
    if tags: query["tags"] = {"$in": tags}
    matching_tasks = list(tasks_col.find(query))
    if not matching_tasks: return f"Error: I couldn't find any task matching all those criteria (title: '{title}', priority: {priority}, tags: {tags})."
    if len(matching_tasks) > 1: return f"Error: I found multiple tasks that still match: {', '.join([f'\"{t["title"]}\"' for t in matching_tasks])}. Please be more specific."
    task_to_delete = matching_tasks[0]; tasks_col.delete_one({"_id": task_to_delete["_id"]}); get_tasks.clear()
    return f"Successfully deleted the task: '{task_to_delete['title']}'."

# --- Theme and CSS (Unchanged) ---
def get_era_theme_config(era):
    themes = {
        "1989": {"bg": "#e0f7fa", "text": "#0d47a1", "btn_bg": "#1976d2", "btn_text": "#ffffff", "cal_bg": "#b3e5fc", "cal_text": "#01579b", "btn_hover": "#1565c0"},
        "Red": {"bg": "#fff0f0", "text": "#c1121f", "btn_bg": "#d32f2f", "btn_text": "#ffffff", "cal_bg": "#ffcdd2", "cal_text": "#b71c1c", "btn_hover": "#c62828"},
        "Lover": {"bg": "#ffe6f0", "text": "#c2185b", "btn_bg": "#ec407a", "btn_text": "#ffffff", "cal_bg": "#f8bbd0", "cal_text": "#880e4f", "btn_hover": "#d81b60"},
        "Folklore": {"bg": "#f0f0f0", "text": "#4a4a4a", "btn_bg": "#757575", "btn_text": "#ffffff", "cal_bg": "#e0e0e0", "cal_text": "#333333", "btn_hover": "#616161"}
    }
    return themes.get(era, themes["Folklore"])

def apply_global_styles():
    if "era_mode" not in st.session_state: st.session_state.era_mode = "Folklore"
    if "theme_mode" not in st.session_state: st.session_state.theme_mode = "light"
    current_theme = get_era_theme_config(st.session_state.era_mode)
    theme_bg = "#0f172a" if st.session_state.theme_mode == "dark" else current_theme["bg"]
    theme_text = "#f8fafc" if st.session_state.theme_mode == "dark" else current_theme["text"]
    theme_surface = "#1e293b" if st.session_state.theme_mode == "dark" else "#ffffff"
    theme_border = "#334155" if st.session_state.theme_mode == "dark" else "#e2e8f0"
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
        .stApp {{ background-color: {theme_bg}; color: {theme_text}; }}
        h1, h2, h3, p, label {{ color: {theme_text} !important; }}
        .stTextInput > div > div > input, .stSelectbox > div > div > div, .stTextArea > div > div > textarea {{ background-color: {theme_surface}; color: {theme_text}; border: 1px solid {theme_border}; }}
        .stButton > button {{ background-color: {current_theme['btn_bg']}; color: {current_theme['btn_text']}; border-radius: 8px; border: none; }}
        .logout-button-container .stButton > button {{ background-color: #d32f2f !important; }}
        .logout-button-container .stButton > button p {{ color: #ffffff !important; }}
        .task-card {{ background-color: {theme_surface}; border: 1px solid {theme_border}; border-radius: 10px; padding: 0.8rem; margin-bottom: 0.6rem; }}
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR LOGIC ---
def build_sidebar():
    if not st.session_state.get("login_state"): return
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.get('user', '')}")
        st.markdown("---")

        st.subheader("🎨 Choose Your Era")
        era_options = ["Folklore", "Lover", "Red", "1989"]
        selected_era = st.selectbox("Era Select", era_options, label_visibility="collapsed", index=era_options.index(st.session_state.get("era_mode", "Folklore")))
        if selected_era != st.session_state.get("era_mode"):
            st.session_state.era_mode = selected_era; st.rerun()

        theme_options = ["light", "dark"]
        selected_theme = st.selectbox("Theme", theme_options, label_visibility="collapsed", index=theme_options.index(st.session_state.get("theme_mode", "light")))
        if selected_theme != st.session_state.get("theme_mode"):
            st.session_state.theme_mode = selected_theme; st.rerun()
        st.markdown("---")

        st.subheader("Stats at a Glance")
        all_tasks = get_tasks(st.session_state.user); total_tasks = len(all_tasks)
        completed_tasks = len([t for t in all_tasks if t['status'] == 'Completed'])
        st.metric("Pending Tasks", total_tasks - completed_tasks); st.metric("Completed Tasks", completed_tasks)

        st.markdown("---")
        st.markdown(f'<div class="logout-button-container">', unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
