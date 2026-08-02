# TaskFlow

TaskFlow is a Streamlit-based productivity app for managing tasks, deadlines, priorities, and tags. It includes a login/signup experience, a task dashboard, and a calendar view, with optional MongoDB storage and a local JSON fallback for demo use.

## Features

- User sign-up and login flow
- Add, edit, and delete tasks
- Priority, due date, and tag-based organization
- Filter and search tasks by status or tag
- Calendar view for due dates
- Theme styling with multiple visual eras

## Quick start

1. Create and activate a virtual environment

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Configure secrets if you want MongoDB support

Create a file named `.streamlit/secrets.toml` and add a MongoDB URI if needed. If you skip this step, the app will run in local demo mode with a JSON file.

4. Start the app

```bash
streamlit run taskflow_app.py
```

## GitHub Pages

A simple landing page for the project is available in the `docs/` folder. To publish it:

1. Make the repository public in GitHub Settings → General → Visibility.
2. Open Settings → Pages.
3. Choose the `docs` folder as the source.
4. Save and wait for the site to publish.

## Notes

- The app stores data locally when no MongoDB connection is configured.
- The generated local data file is ignored by Git to keep the repository clean.
