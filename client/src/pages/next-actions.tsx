import { useItems } from "@/hooks/use-items";
import { useProjects } from "@/hooks/use-projects";
import { ItemRow } from "@/components/item-row";
import { ItemDialog } from "@/components/item-dialog";
import { useState } from "react";
import { Item } from "@shared/schema";

export default function NextActionsPage() {
  const { data: items } = useItems();
  const { data: projects } = useProjects();
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);

  const nextActions = items?.filter(item => item.status === "next") || [];

  // Group by Context
  const groupedItems = nextActions.reduce((acc, item) => {
    const context = item.contexts?.[0] || "No Context";
    if (!acc[context]) acc[context] = [];
    acc[context].push(item);
    return acc;
  }, {} as Record<string, Item[]>);

  const sortedContexts = Object.keys(groupedItems).sort((a, b) => {
    if (a === "No Context") return 1;
    if (b === "No Context") return -1;
    return a.localeCompare(b);
  });

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Next Actions</h1>
          <p className="text-muted-foreground mt-1">Concrete, physical actions to move projects forward.</p>
        </div>
      </div>

      <div className="space-y-8">
        {nextActions.length === 0 && (
          <div className="p-12 border border-dashed rounded-xl text-center text-muted-foreground">
            No next actions. Process your inbox or review projects to generate tasks.
          </div>
        )}

        {sortedContexts.map(context => (
          <section key={context} className="space-y-3">
            <h2 className="text-sm font-semibold text-primary uppercase tracking-wider flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary/40"></span>
              {context}
            </h2>
            <div className="bg-card rounded-xl border shadow-sm divide-y">
              {groupedItems[context].map(item => (
                <ItemRow 
                  key={item.id} 
                  item={item} 
                  project={projects?.find(p => p.id === item.projectId)}
                  onEdit={setSelectedItem}
                />
              ))}
            </div>
          </section>
        ))}
      </div>

      <ItemDialog 
        item={selectedItem} 
        open={!!selectedItem} 
        onClose={() => setSelectedItem(null)} 
        mode="edit"
      />
    </div>
  );
}
