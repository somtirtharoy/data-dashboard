import axios from "axios";

const BASE = import.meta.env.VITE_API_URL ?? "";

export const api = axios.create({ baseURL: `${BASE}/api/v1` });

export interface SpendReport {
  id: number;
  source_file: string;
  ministry: string;
  program: string;
  category: string;
  vendor: string | null;
  fiscal_year: string;
  period_start: string;
  period_end: string;
  amount: string;
  currency: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReportsListResponse {
  total: number;
  page: number;
  page_size: number;
  items: SpendReport[];
}

export interface AnalyticsSummary {
  by_category: { name: string; total: number }[];
  by_ministry: { name: string; total: number }[];
  by_fiscal_year: { name: string; total: number }[];
  total_spend: string;
}

export async function fetchReports(params: {
  page?: number;
  page_size?: number;
  ministry?: string;
  category?: string;
  fiscal_year?: string;
}): Promise<ReportsListResponse> {
  const { data } = await api.get<ReportsListResponse>("/reports", { params });
  return data;
}

export async function fetchAnalytics(fiscal_year?: string): Promise<AnalyticsSummary> {
  const { data } = await api.get<AnalyticsSummary>("/reports/analytics/summary", {
    params: fiscal_year ? { fiscal_year } : {},
  });
  return data;
}
