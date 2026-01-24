import { useItems } from "@/hooks/use-items";
import { ItemRow } from "@/components/item-row";
import { ItemDialog } from "@/components/item-dialog";
import { useState } from "react";
import { Item } from "@shared/schema";

export default function WaitingForPage() {
  const { data: items } = useItems();
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);

  const waitingItems = items?.filter(item => item.status === "waiting") || [];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Waiting For</h1>
      
      <div className="bg-card rounded-xl border shadow-sm divide-y">
        {waitingItems.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground">Nothing currently delegated or pending.</div>
        ) : (
          waitingItems.map(item => (
            <ItemRow 
              key={item.id} 
              item={item} 
              onEdit={setSelectedItem}
            />
          ))
        )}
      </div>

      <ItemDialog 
        item={selectedItem} 
        open={!!selectedItem} 
        onClose={() => setSelectedItem(null)} 
      />
    </div>
  );
}
