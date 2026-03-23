import { useState } from "react";
import { useReports } from "@/hooks/useReports";

export default function ReportsPage() {
  const [page, setPage] = useState(1);
  const [fiscalYear, setFiscalYear] = useState("");
  const [ministry, setMinistry] = useState("");

  const { data, isLoading, isError } = useReports({
    page,
    page_size: 50,
    fiscal_year: fiscalYear || undefined,
    ministry: ministry || undefined,
  });

  return (
    <div>
      <h2>Spend Reports</h2>
      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <input
          placeholder="Filter by ministry"
          value={ministry}
          onChange={(e) => { setMinistry(e.target.value); setPage(1); }}
          style={{ padding: "4px 8px" }}
        />
        <input
          placeholder="Fiscal year (e.g. 2024-25)"
          value={fiscalYear}
          onChange={(e) => { setFiscalYear(e.target.value); setPage(1); }}
          style={{ padding: "4px 8px" }}
        />
      </div>

      {isLoading && <p>Loading...</p>}
      {isError && <p style={{ color: "red" }}>Failed to load reports.</p>}

      {data && (
        <>
          <p>
            Showing {data.items.length} of {data.total} records
          </p>
          <table>
            <thead>
              <tr>
                <th>Ministry</th>
                <th>Program</th>
                <th>Category</th>
                <th>Vendor</th>
                <th>Fiscal Year</th>
                <th>Period Start</th>
                <th>Period End</th>
                <th>Amount</th>
                <th>Currency</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id}>
                  <td>{r.ministry}</td>
                  <td>{r.program}</td>
                  <td>{r.category}</td>
                  <td>{r.vendor ?? "—"}</td>
                  <td>{r.fiscal_year}</td>
                  <td>{r.period_start}</td>
                  <td>{r.period_end}</td>
                  <td>{Number(r.amount).toLocaleString("en-CA", { style: "currency", currency: r.currency })}</td>
                  <td>{r.currency}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
            <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>Page {page}</span>
            <button
              disabled={page * 50 >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
