import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import AnalyticsPage from "@/pages/AnalyticsPage";

vi.mock("@/hooks/useReports", () => ({
  useAnalytics: () => ({
    data: {
      total_spend: "500000",
      by_category: [{ name: "IT", total: 300000 }],
      by_ministry: [{ name: "Finance", total: 500000 }],
      by_fiscal_year: [{ name: "2024-25", total: 500000 }],
    },
    isLoading: false,
    isError: false,
  }),
}));

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient();
  return (
    <MemoryRouter>
      <QueryClientProvider client={qc}>{children}</QueryClientProvider>
    </MemoryRouter>
  );
}

describe("AnalyticsPage", () => {
  it("renders total spend", () => {
    render(<AnalyticsPage />, { wrapper });
    expect(screen.getByText(/Total Spend/i)).toBeInTheDocument();
  });

  it("renders chart headings", () => {
    render(<AnalyticsPage />, { wrapper });
    expect(screen.getByText("Spend by Category")).toBeInTheDocument();
    expect(screen.getByText("Spend by Ministry")).toBeInTheDocument();
  });
});
