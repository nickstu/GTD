import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, buildUrl, type CreateItemRequest, type UpdateItemRequest } from "@shared/routes";
import { useToast } from "@/hooks/use-toast";

export function useItems() {
  return useQuery({
    queryKey: [api.items.list.path],
    queryFn: async () => {
      const res = await fetch(api.items.list.path, { credentials: "include" });
      if (!res.ok) throw new Error("Failed to fetch items");
      return api.items.list.responses[200].parse(await res.json());
    },
  });
}

export function useItem(id: number) {
  return useQuery({
    queryKey: [api.items.get.path, id],
    queryFn: async () => {
      const url = buildUrl(api.items.get.path, { id });
      const res = await fetch(url, { credentials: "include" });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error("Failed to fetch item");
      return api.items.get.responses[200].parse(await res.json());
    },
    enabled: !!id,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (data: CreateItemRequest) => {
      // Validate with shared schema before sending if possible, or just send
      const res = await fetch(api.items.create.path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        credentials: "include",
      });

      if (!res.ok) {
        if (res.status === 400) {
          const error = api.items.create.responses[400].parse(await res.json());
          throw new Error(error.message);
        }
        throw new Error("Failed to create item");
      }
      return api.items.create.responses[201].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.items.list.path] });
      toast({ title: "Item captured", description: "Added to your inbox." });
    },
    onError: (err) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
  });
}

export function useUpdateItem() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async ({ id, ...updates }: { id: number } & UpdateItemRequest) => {
      const url = buildUrl(api.items.update.path, { id });
      const res = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(updates),
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error("Failed to update item");
      }
      return api.items.update.responses[200].parse(await res.json());
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.items.list.path] });
    },
    onError: (err) => {
      toast({ title: "Error", description: err.message, variant: "destructive" });
    }
  });
}

export function useDeleteItem() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async (id: number) => {
      const url = buildUrl(api.items.delete.path, { id });
      const res = await fetch(url, { method: "DELETE", credentials: "include" });
      if (!res.ok) throw new Error("Failed to delete item");
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [api.items.list.path] });
      toast({ title: "Deleted", description: "Item removed." });
    },
  });
}
