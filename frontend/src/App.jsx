
import { useEffect, useState } from "react";
import axios from "axios";
import {
  Wallet,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Upload,
  LayoutDashboard,
  Receipt,
  ChartNoAxesCombined,
  RefreshCw,
  Menu,
  X,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";

function money(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

export default function App() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [trends, setTrends] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [summaryRes, categoriesRes, trendsRes, transactionsRes] =
        await Promise.all([
          axios.get(`${API}/api/analytics/summary`, {
            params: { year, month },
          }),
          axios.get(`${API}/api/analytics/categories`, {
            params: { year, month },
          }),
          axios.get(`${API}/api/analytics/monthly-trends`, {
            params: { months: 6 },
          }),
          axios.get(`${API}/api/analytics/recent-transactions`, {
            params: { limit: 8 },
          }),
        ]);

      setSummary(summaryRes.data);
      setCategories(
        Array.isArray(categoriesRes.data)
          ? categoriesRes.data
          : categoriesRes.data.categories || []
      );
      setTrends(
        Array.isArray(trendsRes.data)
          ? trendsRes.data
          : trendsRes.data.trends || []
      );
      setTransactions(
        Array.isArray(transactionsRes.data)
          ? transactionsRes.data
          : transactionsRes.data.transactions || []
      );
    } catch (err) {
      console.error(err);
      setError(
        "Couldn't load dashboard data. Check that FastAPI is running and its CORS settings allow http://localhost:5173."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, [year, month]);

  async function importCSV(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setNotice("");
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await axios.post(
        `${API}/api/transactions/import`,
        formData
      );

      const count =
        response.data.imported_count ??
        response.data.imported ??
        response.data.created_count ??
        0;

      setNotice(
        `Import completed. ${count} transactions imported.`
      );
      await loadDashboard();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(
        typeof detail === "string"
          ? detail
          : "Import failed. Check the CSV format or whether this file was already imported."
      );
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  const monthLabel = new Date(year, month - 1, 1).toLocaleDateString(
    "en-IN",
    { month: "long", year: "numeric" }
  );

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-icon"><Wallet size={23} /></div>
          <div>
            <h1>SpendSense</h1>
            <p>Personal finance</p>
          </div>
          <button
            className="mobile-close icon-button"
            onClick={() => setMenuOpen(false)}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <p className="nav-label">WORKSPACE</p>
        <button className="nav-item active" onClick={() => setMenuOpen(false)}>
          <LayoutDashboard size={19} /> Dashboard
        </button>
        <button
          className="nav-item"
          onClick={() =>
            document.getElementById("transactions")?.scrollIntoView({
              behavior: "smooth",
            })
          }
        >
          <Receipt size={19} /> Transactions
        </button>
        <button
          className="nav-item"
          onClick={() =>
            document.getElementById("analytics")?.scrollIntoView({
              behavior: "smooth",
            })
          }
        >
          <ChartNoAxesCombined size={19} /> Analytics
        </button>

        <div className="sidebar-bottom">
          <div className="sidebar-tip">
            <div className="tip-icon"><TrendingUp size={19} /></div>
            <strong>Build better habits</strong>
            <p>Understand your spending, one transaction at a time.</p>
          </div>
          <p className="version">SpendSense · Personal Edition</p>
        </div>
      </aside>

      {menuOpen && (
        <button
          className="mobile-overlay"
          aria-label="Close navigation"
          onClick={() => setMenuOpen(false)}
        />
      )}

      <main className="main-content">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="mobile-menu icon-button"
              onClick={() => setMenuOpen(true)}
              aria-label="Open menu"
            >
              <Menu size={22} />
            </button>
            <div>
              <p className="eyebrow">YOUR MONEY, CLEARER</p>
              <h2>Financial overview</h2>
            </div>
          </div>
          <div className="topbar-actions">
            <select
              aria-label="Select month"
              value={month}
              onChange={(e) => setMonth(Number(e.target.value))}
            >
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {new Date(2000, i, 1).toLocaleDateString("en-IN", {
                    month: "long",
                  })}
                </option>
              ))}
            </select>
            <select
              aria-label="Select year"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
            >
              {[today.getFullYear(), today.getFullYear() - 1,
                today.getFullYear() - 2].map((y) => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
            <button
              className="icon-button refresh-button"
              onClick={loadDashboard}
              aria-label="Refresh dashboard"
              title="Refresh"
            >
              <RefreshCw size={18} />
            </button>
          </div>
        </header>

        <section className="welcome-row">
          <div>
            <h3>Here's your money snapshot.</h3>
            <p>Review your financial activity for {monthLabel}.</p>
          </div>
          <label className="primary-button upload-button">
            <Upload size={17} />
            {uploading ? "Importing..." : "Import CSV"}
            <input
              type="file"
              accept=".csv,text/csv"
              hidden
              disabled={uploading}
              onChange={importCSV}
            />
          </label>
        </section>

        {notice && <div className="notice success-notice">{notice}</div>}
        {error && <div className="notice error-notice">{error}</div>}

        {loading && !summary ? (
          <div className="loading-state">Loading your financial overview...</div>
        ) : (
          <>
            <section className="stats-grid">
              <StatCard
                title="Total income"
                amount={money(summary?.total_income)}
                icon={<TrendingUp size={21} />}
                color="green"
                note="Money received"
              />
              <StatCard
                title="Total expenses"
                amount={money(summary?.total_expenses)}
                icon={<TrendingDown size={21} />}
                color="red"
                note="Money spent"
              />
              <StatCard
                title="Net balance"
                amount={money(summary?.balance)}
                icon={<Wallet size={21} />}
                color="blue"
                note="Income minus expenses"
              />
              <StatCard
                title="Transactions"
                amount={summary?.transaction_count ?? 0}
                icon={<Receipt size={21} />}
                color="purple"
                note="In selected month"
              />
            </section>

            <section className="analytics-grid" id="analytics">
              <div className="panel trend-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Income vs expenses</h3>
                    <p>Your six-month financial trend</p>
                  </div>
                  <span className="panel-icon"><ChartNoAxesCombined size={19} /></span>
                </div>
                <div className="chart-area">
                  {trends.length ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={trends}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e9edf3" />
                        <XAxis dataKey="month" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
                        <YAxis
                          tick={{ fontSize: 11 }}
                          axisLine={false}
                          tickLine={false}
                          tickFormatter={(v) => v >= 1000 ? `₹${v / 1000}k` : `₹${v}`}
                        />
                        <Tooltip formatter={(v) => money(v)} />
                        <Bar dataKey="income" name="Income" fill="#16a34a" radius={[5, 5, 0, 0]} />
                        <Bar dataKey="expenses" name="Expenses" fill="#f97362" radius={[5, 5, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <EmptyState text="Your monthly trends will appear here." />
                  )}
                </div>
              </div>

              <div className="panel category-panel">
                <div className="panel-heading">
                  <div>
                    <h3>Spending breakdown</h3>
                    <p>Where your money goes</p>
                  </div>
                  <span className="panel-icon"><Wallet size={19} /></span>
                </div>
                <div className="category-list">
                  {categories.length ? categories.map((item, index) => {
                    const name = item.category ?? item.name ?? "Other";
                    const amount = item.total ?? item.amount ?? item.total_amount ?? 0;
                    const percentage = item.percentage ??
                      (summary?.total_expenses
                        ? (Number(amount) / summary.total_expenses) * 100
                        : 0);
                    return (
                      <div className="category-item" key={`${name}-${index}`}>
                        <div className="category-topline">
                          <span>{name}</span>
                          <strong>{money(amount)}</strong>
                        </div>
                        <div className="progress-track">
                          <div
                            className="progress-fill"
                            style={{ width: `${Math.min(100, Math.max(0, Number(percentage)))}%` }}
                          />
                        </div>
                      </div>
                    );
                  }) : (
                    <EmptyState text="Import transactions to see your spending categories." />
                  )}
                </div>
              </div>
            </section>

            <section className="panel transactions-panel" id="transactions">
              <div className="panel-heading transaction-heading">
                <div>
                  <h3>Recent transactions</h3>
                  <p>Your latest recorded financial activity</p>
                </div>
                <span className="transaction-count">
                  {transactions.length} records
                </span>
              </div>

              {transactions.length ? (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Transaction</th>
                        <th>Category</th>
                        <th>Date</th>
                        <th>Type</th>
                        <th className="amount-column">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((tx, index) => {
                        const isIncome = String(tx.transaction_type).toLowerCase() === "income";
                        return (
                          <tr key={tx.id ?? index}>
                            <td>
                              <div className="transaction-name">
                                <span className={`transaction-icon ${isIncome ? "income-icon" : "expense-icon"}`}>
                                  {isIncome
                                    ? <ArrowDownRight size={17} />
                                    : <ArrowUpRight size={17} />}
                                </span>
                                <strong>{tx.description}</strong>
                              </div>
                            </td>
                            <td><span className="category-tag">{tx.category || "Other"}</span></td>
                            <td>{tx.transaction_date ? String(tx.transaction_date).slice(0, 10) : "—"}</td>
                            <td>
                              <span className={`type-tag ${isIncome ? "type-income" : "type-expense"}`}>
                                {isIncome ? "Income" : "Expense"}
                              </span>
                            </td>
                            <td className={`amount-column amount ${isIncome ? "income-text" : "expense-text"}`}>
                              {isIncome ? "+" : "−"}{money(tx.amount)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState text="No transactions yet. Import a CSV statement to get started." />
              )}
            </section>

            <footer className="footer">
              <span>SpendSense · Personal finance, made clearer.</span>
              <span>Data stored in your PostgreSQL database</span>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

function StatCard({ title, amount, icon, color, note }) {
  return (
    <div className="stat-card">
      <div className="stat-topline">
        <span className={`stat-icon ${color}`}>{icon}</span>
        <span className="stat-note">{note}</span>
      </div>
      <p className="stat-title">{title}</p>
      <h3>{amount}</h3>
    </div>
  );
}

function EmptyState({ text }) {
  return <div className="empty-state">{text}</div>;
}
