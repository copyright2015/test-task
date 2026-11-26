@echo off
setlocal
python --version >nul 2>&1 || (echo Python 3.10 or newer is required. & exit /b 1)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" || (echo Python 3.10 or newer is required. & exit /b 1)
node --version >nul 2>&1 || (echo Node.js 18 or newer is required. & exit /b 1)
node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 18 ? 0 : 1)" || (echo Node.js 18 or newer is required. & exit /b 1)

if not exist .venv\Scripts\python.exe python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r backend\requirements.txt || exit /b 1
if not exist frontend\node_modules (
  pushd frontend
  call npm install
  if errorlevel 1 exit /b 1
  popd
)
if not exist database mkdir database
python -m alembic -c backend\alembic.ini upgrade head || exit /b 1

start "Campaign Manager API" cmd /k "call .venv\Scripts\activate.bat && uvicorn app.main:app --app-dir backend --reload"
start "Campaign Manager UI" cmd /k "cd /d frontend && npm run dev"
