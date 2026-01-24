import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@shared/routes";
import { useToast } from "@/hooks/use-toast";

export function useSystemExport() {
  return useQuery({
    queryKey: [api.system.export.path],
    queryFn: async () => {
      const res = await fetch(api.system.export.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to export data");
      return api.system.export.responses[200].parse(await res.json());
    },
    enabled: false, // Only run manually
  });
}

export function useSystemImport() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: { projects: any[]; items: any[] }) => {
      const res = await fetch(api.system.import.path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });
      if (!res.ok) throw new Error("Failed to import data");
      return api.system.import.responses[200].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries();
      toast({ title: "Import successful", description: "Your data has been restored." });
    },
    onError: (error) => {
      toast({ title: "Import failed", description: error.message, variant: "destructive" });
    }
  });
}
