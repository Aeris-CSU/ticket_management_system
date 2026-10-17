## Running the backend after cloning (Windows / PowerShell)

Each teammate needs their own Python environment, PostgreSQL database, and local configuration. Cloning the repository does not copy the database or your installed packages.

### 1. Install the prerequisites

- Git: https://git-scm.com/downloads
- Python 3.13: https://www.python.org/downloads/ (the existing local environment uses Python 3.13.5).
- PostgreSQL and pgAdmin: https://www.postgresql.org/download/windows/

During PostgreSQL installation, remember the password you choose for the `postgres` user. Start the PostgreSQL service before continuing. The default port is `5432`.

### 2. Clone the repository

Open PowerShell in the folder where you want the project:

```powershell
git clone https://github.com/Jdeexon/ticket_management_system.git
cd ticket_management_system
```

If you already cloned it, open the repository folder and run `git pull` instead.

### 3. Create a fresh virtual environment and install dependencies

Run these commands from the repository root, where `requirements.txt` is located:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

Use your new `.venv`; an environment copied from another computer is not portable. If PowerShell blocks activation, allow it for this terminal session, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

In VS Code, select `.venv\Scripts\python.exe` using **Python: Select Interpreter**.

### 4. Create the local PostgreSQL database

In pgAdmin, connect to your local PostgreSQL server using your own `postgres` password. Open Query Tool on the existing `postgres` database and run this statement once:

```sql
CREATE DATABASE ticket_system;
```

Alternatively, if PostgreSQL's `psql` command is available in your terminal:

```powershell
psql -U postgres -h localhost -p 5432 -d postgres -c "CREATE DATABASE ticket_system;"
```

If the database already exists, skip its creation. Django's migrations create the tables in the next steps; do not manually create the tables.

### 5. Set your PostgreSQL password

Debug mode, a development secret key, and localhost hosts are already configured in `ticket_system/ticket_system/settings.py`. You do not need to set `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, or `DJANGO_ALLOWED_HOSTS` before starting the server.

Replace `YOUR_POSTGRES_PASSWORD` with the password you set during PostgreSQL installation:

```powershell
$env:DB_PASSWORD = 'YOUR_POSTGRES_PASSWORD'
```

The database defaults are already `ticket_system`, user `postgres`, host `localhost`, and port `5432`. The password command applies only to the current terminal, so run it again when opening a new terminal. A `.env` file is not automatically loaded by this backend.

If you used a different database name, username, or port, also set the corresponding variable before running Django:

```powershell
$env:DB_NAME = 'your_database_name'
$env:DB_USER = 'your_postgres_username'
$env:DB_PORT = 'your_postgres_port'
```

### 6. Apply the committed migrations

Enter the backend directory containing `manage.py`:

```powershell
cd ticket_system
python manage.py check
python manage.py migrate
python manage.py showmigrations
```

Applied migrations should have `[X]` beside them. A fresh clone uses the migration files already committed to the repository, so `makemigrations` is not needed for initial setup. Do not delete migrations or run the migration-removal script as part of setup.

### 7. Sign in with the predefined local administrator

Running `python manage.py migrate` creates this administrator for local testing:

- Username: `localadmin`
- Password: `TickarlaAdmin123!`

Each teammate gets their own account in their own laptop's database. No `createsuperuser` or role-setting command is needed for this account. It has the application's `ADMIN` role; it is not a Django superuser.

To change the password, sign in, click your profile (avatar/name) in the dashboard header, and enter the current password, new password, and confirmation. You will return to login after saving.

The default password is stored as a hash in the database. Running migrations again does not reset a changed password or overwrite an existing `localadmin` account.

If you forget your changed password, run this from the backend folder:

```powershell
python manage.py changepassword localadmin
```

### 8. Start the backend

```powershell
python manage.py runserver
```

Leave this terminal running. The backend listens at `http://127.0.0.1:8000/`, with API endpoints under `/api/`. The root URL `/` and `/admin/` are not configured in this project, so a 404 at either URL does not mean the server failed.

To verify login from a second PowerShell terminal, enter the password you chose for your local administrator:

```powershell
$loginCredential = Get-Credential -UserName localadmin -Message 'Enter your local administrator password'
$loginBody = @{
    username = $loginCredential.UserName
    password = $loginCredential.GetNetworkCredential().Password
} | ConvertTo-Json
$loginResponse = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/login/' -Method Post -ContentType 'application/json' -Body $loginBody
$loginResponse.account
```

A successful response includes your account with role `ADMIN`; the response also contains access and refresh tokens. Other protected requests need the access token as a Bearer token.

### Starting it again later

From the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
$env:DB_PASSWORD = 'YOUR_POSTGRES_PASSWORD'
cd ticket_system
python manage.py migrate
python manage.py runserver
```

You do not need to recreate the database or administrator each time. After pulling changes to `requirements.txt`, run `python -m pip install -r requirements.txt` from the repository root again.

If you changed the database name, username, or port in step 5, set those variables again in the new terminal too.

### Common setup errors

| Error or symptom | What to check |
| --- | --- |
| `No module named django` | Activate `.venv` and install `requirements.txt` using that environment's Python. |
| PostgreSQL password authentication failed | Set `DB_PASSWORD` to your own local PostgreSQL password. |
| Database `ticket_system` does not exist | Create the database in step 4. |
| Connection refused on port 5432 | Start the PostgreSQL service and check `DB_HOST` and `DB_PORT`. |
| Missing database tables | Run `python manage.py migrate` against the configured database. |
| Login succeeds but administrator actions return 403 | Set the account's custom role to `ADMIN` as shown in step 7. |
| `psql` is not recognized | Use pgAdmin's Query Tool or add PostgreSQL's `bin` directory to PATH. |
| Package installation reports no matching version | Check Python and the package-index configuration; share the exact failing package and error with the maintainer. Keep the committed pins until compatibility is checked. |
| `psycopg2` compilation fails | Its source package may require PostgreSQL development tools and a C compiler; share the install error with the maintainer before changing dependencies. |
| Port 8000 is already in use | Run `python manage.py runserver 8001` and use port 8001 in your API/frontend configuration. |


