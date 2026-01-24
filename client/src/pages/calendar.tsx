import { useItems } from "@/hooks/use-items";
import { ItemRow } from "@/components/item-row";
import { ItemDialog } from "@/components/item-dialog";
import { useState } from "react";
import { Item } from "@shared/schema";
import { format, isSameDay, startOfToday, addDays } from "date-fns";

export default function CalendarPage() {
  const { data: items } = useItems();
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);

  // Filter items that have due dates
  const calendarItems = items?.filter(item => item.dueDatetime) || [];
  
  // Sort by date
  calendarItems.sort((a, b) => new Date(a.dueDatetime!).getTime() - new Date(b.dueDatetime!).getTime());

  // Generate next 7 days for view
  const today = startOfToday();
  const next7Days = Array.from({ length: 7 }, (_, i) => addDays(today, i));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Calendar</h1>
        <p className="text-muted-foreground">Hard landscape: items that MUST happen on specific days.</p>
      </div>

      <div className="grid gap-6">
        {next7Days.map(date => {
          const daysItems = calendarItems.filter(item => 
            item.dueDatetime && isSameDay(new Date(item.dueDatetime), date)
          );
          
          if (daysItems.length === 0) return null;

          return (
            <div key={date.toString()} className="space-y-2">
               <h3 className="font-semibold text-lg flex items-center gap-2">
                 <span className="text-primary">{format(date, "EEEE")}</span>
                 <span className="text-muted-foreground font-normal">{format(date, "MMM do")}</span>
               </h3>
               <div className="bg-card rounded-xl border shadow-sm divide-y">
                 {daysItems.map(item => (
                   <ItemRow key={item.id} item={item} onEdit={setSelectedItem} />
                 ))}
               </div>
            </div>
          );
        })}
        
        {/* Future items */}
        <div className="pt-8">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">Future</h3>
          <div className="bg-card rounded-xl border shadow-sm divide-y">
            {calendarItems
               .filter(item => new Date(item.dueDatetime!) > addDays(today, 7))
               .map(item => (
                 <ItemRow key={item.id} item={item} onEdit={setSelectedItem} />
               ))}
          </div>
        </div>
      </div>

      <ItemDialog 
        item={selectedItem} 
        open={!!selectedItem} 
        onClose={() => setSelectedItem(null)} 
      />
    </div>
  );
}
