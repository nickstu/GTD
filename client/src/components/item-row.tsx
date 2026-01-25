import { Item, Project } from "@shared/schema";
import { format } from "date-fns";
import { Calendar, Clock, Tag, AlertCircle } from "lucide-react";
import { useUpdateItem } from "@/hooks/use-items";
import { clsx } from "clsx";

interface ItemRowProps {
  item: Item;
  project?: Project;
  onEdit?: (item: Item) => void;
  showStatus?: boolean;
}

export function ItemRow({ item, project, onEdit, showStatus = false }: ItemRowProps) {
  const updateItem = useUpdateItem();

  const handleComplete = (e: React.MouseEvent) => {
    e.stopPropagation();
    updateItem.mutate({ id: item.id, status: item.status === "done" ? "next" : "done" });
  };

  return (
    <div 
      onClick={() => onEdit?.(item)}
      className="group flex items-start gap-2 p-2 rounded hover:bg-muted/50 transition-colors cursor-pointer border border-transparent hover:border-border/50 text-sm select-none"
    >
      <button 
        onClick={handleComplete}
        className={clsx(
          "mt-0.5 w-4 h-4 rounded border flex items-center justify-center transition-all flex-shrink-0",
          item.status === "done" 
            ? "bg-primary border-primary text-primary-foreground" 
            : "border-muted-foreground/30 hover:border-primary"
        )}
      >
        {item.status === "done" && <span className="text-[10px] font-bold">✓</span>}
      </button>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 overflow-hidden">
          <span className={clsx("font-medium truncate", item.status === "done" && "line-through text-muted-foreground")}>
            {item.title}
          </span>
        </div>
        
        {(item.dueDatetime || project) && (
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-muted-foreground mt-0.5">
            {project && (
              <span className="flex items-center gap-1 text-primary/80">
                <span className="w-1 h-1 rounded-full bg-primary/40"></span>
                {project.name}
              </span>
            )}
            
            {item.dueDatetime && (
              <span className={clsx(
                "flex items-center gap-1", 
                new Date(item.dueDatetime) < new Date() ? "text-destructive" : "text-amber-600"
              )}>
                <Clock className="w-2.5 h-2.5" />
                {format(new Date(item.dueDatetime), "MMM d")}
                {item.startTime && (
                  <span className="ml-1 opacity-80">
                    {item.startTime}
                  </span>
                )}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
