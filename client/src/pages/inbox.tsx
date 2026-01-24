import { useItems } from "@/hooks/use-items";
import { ItemRow } from "@/components/item-row";
import { ItemDialog } from "@/components/item-dialog";
import { useState } from "react";
import { Item } from "@shared/schema";
import { Inbox as InboxIcon } from "lucide-react";

export default function InboxPage() {
  const { data: items, isLoading } = useItems();
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);

  const inboxItems = items?.filter(item => item.status === "inbox") || [];

  if (isLoading) return <div className="p-8 text-muted-foreground">Loading inbox...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Inbox</h1>
        <span className="text-muted-foreground text-sm font-medium">{inboxItems.length} items</span>
      </div>

      <div className="bg-card rounded-xl border shadow-sm divide-y">
        {inboxItems.length === 0 ? (
          <div className="p-12 flex flex-col items-center justify-center text-center text-muted-foreground">
            <InboxIcon className="w-12 h-12 mb-4 opacity-20" />
            <h3 className="text-lg font-medium">Inbox Zero!</h3>
            <p className="max-w-xs mt-2 text-sm">You've processed everything. Great job capturing and clarifying your world.</p>
          </div>
        ) : (
          inboxItems.map(item => (
            <div key={item.id} className="relative group">
              <ItemRow 
                item={item} 
                onEdit={(item) => setSelectedItem(item)} 
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={() => setSelectedItem(item)}
                  className="bg-primary text-primary-foreground text-xs font-bold px-3 py-1.5 rounded-full shadow-lg hover:scale-105 transition-transform"
                >
                  Process
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <ItemDialog 
        item={selectedItem} 
        open={!!selectedItem} 
        onClose={() => setSelectedItem(null)} 
        mode="process" // Critical: Inbox uses "process" mode
      />
    </div>
  );
}
