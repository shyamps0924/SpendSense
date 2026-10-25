# SpendSense — Personal Finance Tracker

SpendSense is a full-stack personal finance application that helps users track income, analyze expenses, and understand their spending habits through an interactive dashboard.

## Features

- Import transactions from CSV statements
- Validate transaction data and detect duplicate file imports
- Automatically categorize transactions using Python-based rules
- Track total income, expenses, and net balance
- Analyze spending by category
- View monthly income and expense trends
- Review recent transactions
- Interactive, responsive dashboard

## Tech Stack

**Frontend**
- React
- Vite
- Recharts
- Axios
- Lucide React

**Backend**
- Python
- FastAPI
- SQLAlchemy

**Database**
- PostgreSQL

## Project Structure

```text
SpendSense/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── analytics.py
│   ├── csv_importer.py
│   ├── categorizer.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── package-lock.json
├── .gitignore
└── README.md
```

## Prerequisites

- Python
- Node.js and npm
- PostgreSQL

## Local Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd SpendSense
```

### 2. Configure the backend

Create and activate a Python virtual environment inside `backend/`.

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a PostgreSQL database and application user. Copy `.env.example` to `.env` and enter your local database credentials.

Start the backend:

```bash
cd backend
fastapi dev main.py
```

The API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Configure the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

Ensure the backend is running and its CORS settings allow the frontend origin.

## Security

- Never commit `.env` files, passwords, API keys, or personal financial statements.
- Use synthetic transaction data for examples and screenshots.
- Configure appropriate authentication and access controls before exposing the backend publicly.

## Current Status

The CSV import, transaction storage, analytics endpoints, and React dashboard are implemented and tested locally.

## Future Improvements

- Budget tracking and spending alerts
- Improved transaction classification
- Android APK packaging
- Deployment for remote access

## License

Choose a license before publishing if you want others to know how they may use, modify, and distribute your code.
