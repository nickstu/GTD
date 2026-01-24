import { useItems } from "@/hooks/use-items";
import { ItemRow } from "@/components/item-row";
import { ItemDialog } from "@/components/item-dialog";
import { useState } from "react";
import { Item } from "@shared/schema";
import { Archive } from "lucide-react";

export default function SomedayPage() {
  const { data: items } = useItems();
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);
  
  const somedayItems = items?.filter(item => item.status === "someday") || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Someday / Maybe</h1>
        <p className="text-muted-foreground">Ideas and projects to consider for the future.</p>
      </div>
      
      <div className="bg-card rounded-xl border shadow-sm divide-y">
        {somedayItems.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground flex flex-col items-center">
            <Archive className="w-12 h-12 mb-4 opacity-20" />
            <p>Empty list.</p>
          </div>
        ) : (
          somedayItems.map(item => (
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
