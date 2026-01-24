import { useItems } from "@/hooks/use-items";
import { ItemRow } from "@/components/item-row";
import { ItemDialog } from "@/components/item-dialog";
import { useState } from "react";
import { Item } from "@shared/schema";
import { BookOpen } from "lucide-react";

export default function ReferencePage() {
  const { data: items } = useItems();
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);
  
  const referenceItems = items?.filter(item => item.status === "reference") || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Reference</h1>
        <p className="text-muted-foreground">Non-actionable information to keep.</p>
      </div>
      
      <div className="bg-card rounded-xl border shadow-sm divide-y">
        {referenceItems.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground flex flex-col items-center">
            <BookOpen className="w-12 h-12 mb-4 opacity-20" />
            <p>No reference items stored.</p>
          </div>
        ) : (
          referenceItems.map(item => (
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
