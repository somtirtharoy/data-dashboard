import { useQuery } from "@tanstack/react-query";
import { fetchReports, fetchAnalytics } from "@/services/api";

export function useReports(params: {
  page: number;
  page_size: number;
  ministry?: string;
  category?: string;
  fiscal_year?: string;
}) {
  return useQuery({
    queryKey: ["reports", params],
    queryFn: () => fetchReports(params),
  });
}

export function useAnalytics(fiscal_year?: string) {
  return useQuery({
    queryKey: ["analytics", fiscal_year],
    queryFn: () => fetchAnalytics(fiscal_year),
  });
}
