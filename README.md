# Daily Progress & Performance Tracker

A productivity application built with **Django** and **Turso (libSQL/Cloud SQLite)**, with a clean UI supporting daily tracking, weekly/monthly progress aggregation, search, and CSV/JSON backups.

---

## 🚀 Running Locally

1. **Activate the virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     .\.venv\Scripts\activate.bat
     ```
   - **Mac/Linux:**
     ```bash
     source .venv/bin/activate
     ```

2. **Run migrations (uses local SQLite automatically):**
   ```bash
   python manage.py migrate
   ```

3. **(Optional) Create admin user:**
   ```bash
   python manage.py createsuperuser
   ```

4. **Start the development server:**
   ```bash
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.
   Django Admin is at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

---

## ☁️ Connecting Turso (Cloud Database)

1. Create a free database in [Turso Dashboard](https://turso.tech) or via CLI:
   ```bash
   turso db create daily-records
   ```

2. Get your Database URL and Auth Token:
   ```bash
   turso db show daily-records --url
   # Example: libsql://daily-records-username.turso.io

   turso db tokens create daily-records
   ```

3. Add them as environment variables (in `.env` or on Render):
   ```ini
   TURSO_DATABASE_URL=libsql://daily-records-username.turso.io
   TURSO_AUTH_TOKEN=your-turso-token-here
   ```

*When these two variables are provided, Django automatically routes all queries to Turso Cloud. If omitted, it automatically uses local `db.sqlite3`!*

---

## 🌐 Deploying to Render (Free Web Service)

1. Push this project to a GitHub repository.
2. In [Render Dashboard](https://dashboard.render.com), click **New +** -> **Web Service** and connect your GitHub repo.
3. Configure the settings:
   - **Environment:** `Python`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate
     ```
   - **Start Command:**
     ```bash
     gunicorn core.wsgi:application
     ```
4. Under **Environment Variables**, add:
   - `SECRET_KEY`: (any random secret string)
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*`
   - `TURSO_DATABASE_URL`: `libsql://your-db-url.turso.io`
   - `TURSO_AUTH_TOKEN`: `your-turso-token`
5. Click **Create Web Service**. Your app is live!
