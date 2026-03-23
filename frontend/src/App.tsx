import { Routes, Route, NavLink } from "react-router-dom";
import ReportsPage from "@/pages/ReportsPage";
import AnalyticsPage from "@/pages/AnalyticsPage";

export default function App() {
  return (
    <div style={{ fontFamily: "sans-serif", maxWidth: 1200, margin: "0 auto", padding: 16 }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0 }}>BCGov Data Dashboard</h1>
        <nav style={{ marginTop: 8, display: "flex", gap: 16 }}>
          <NavLink to="/">Reports</NavLink>
          <NavLink to="/analytics">Analytics</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<ReportsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
        </Routes>
      </main>
    </div>
  );
}
