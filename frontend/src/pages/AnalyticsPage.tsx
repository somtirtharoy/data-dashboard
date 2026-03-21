import { useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useAnalytics } from "@/hooks/useReports";

const COLORS = ["#003366", "#e3a82b", "#5c88da", "#74c476", "#fd8d3c", "#9e9ac8"];

export default function AnalyticsPage() {
  const [fiscalYear, setFiscalYear] = useState("");
  const { data, isLoading, isError } = useAnalytics(fiscalYear || undefined);

  return (
    <div>
      <h2>Analytics</h2>

      <div style={{ marginBottom: 16 }}>
        <input
          placeholder="Fiscal year (e.g. 2024-25)"
          value={fiscalYear}
          onChange={(e) => setFiscalYear(e.target.value)}
          style={{ padding: "4px 8px" }}
        />
      </div>

      {isLoading && <p>Loading analytics...</p>}
      {isError && <p style={{ color: "red" }}>Failed to load analytics.</p>}

      {data && (
        <>
          <p>
            <strong>Total Spend: </strong>
            {Number(data.total_spend).toLocaleString("en-CA", {
              style: "currency",
              currency: "CAD",
            })}
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32 }}>
            {/* Spend by Category — Pie Chart */}
            <section>
              <h3>Spend by Category</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={data.by_category}
                    dataKey="total"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name }) => name}
                  >
                    {data.by_category.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => v.toLocaleString("en-CA", { style: "currency", currency: "CAD" })} />
                </PieChart>
              </ResponsiveContainer>
            </section>

            {/* Spend by Ministry — Bar (Histogram-style) */}
            <section>
              <h3>Spend by Ministry</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.by_ministry} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    tickFormatter={(v) =>
                      `$${(v / 1_000_000).toFixed(1)}M`
                    }
                  />
                  <YAxis type="category" dataKey="name" width={130} />
                  <Tooltip
                    formatter={(v: number) =>
                      v.toLocaleString("en-CA", { style: "currency", currency: "CAD" })
                    }
                  />
                  <Legend />
                  <Bar dataKey="total" fill="#003366" name="Total Spend" />
                </BarChart>
              </ResponsiveContainer>
            </section>

            {/* Spend by Fiscal Year — Bar Chart */}
            <section style={{ gridColumn: "1 / -1" }}>
              <h3>Spend by Fiscal Year</h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.by_fiscal_year}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis tickFormatter={(v) => `$${(v / 1_000_000).toFixed(1)}M`} />
                  <Tooltip
                    formatter={(v: number) =>
                      v.toLocaleString("en-CA", { style: "currency", currency: "CAD" })
                    }
                  />
                  <Bar dataKey="total" fill="#e3a82b" name="Total Spend" />
                </BarChart>
              </ResponsiveContainer>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
