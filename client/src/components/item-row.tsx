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
      className="group flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer border border-transparent hover:border-border/50"
    >
      <button 
        onClick={handleComplete}
        className={clsx(
          "mt-0.5 w-5 h-5 rounded border flex items-center justify-center transition-all",
          item.status === "done" 
            ? "bg-primary border-primary text-primary-foreground" 
            : "border-muted-foreground/30 hover:border-primary"
        )}
      >
        {item.status === "done" && <span className="text-xs font-bold">✓</span>}
      </button>

      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center gap-2">
          <span className={clsx("font-medium text-sm", item.status === "done" && "line-through text-muted-foreground")}>
            {item.title}
          </span>
          {showStatus && item.status !== "next" && item.status !== "done" && (
             <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
               {item.status}
             </span>
          )}
        </div>
        
        {(item.contexts?.length || item.timeEstimate || item.dueDatetime || project || item.notes) && (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
            {project && (
              <span className="flex items-center gap-1 text-primary/80 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-primary/40"></span>
                {project.name}
              </span>
            )}
            
            {item.contexts?.map(ctx => (
              <span key={ctx} className="flex items-center gap-1 text-sky-600 dark:text-sky-400 bg-sky-50 dark:bg-sky-950/30 px-1.5 rounded">
                <Tag className="w-3 h-3" />
                {ctx}
              </span>
            ))}
            
            {item.timeEstimate && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {item.timeEstimate}
              </span>
            )}
            
            {item.dueDatetime && (
              <span className={clsx(
                "flex items-center gap-1", 
                new Date(item.dueDatetime) < new Date() ? "text-destructive" : "text-amber-600 dark:text-amber-400"
              )}>
                <Calendar className="w-3 h-3" />
                {format(new Date(item.dueDatetime), "MMM d, h:mm a")}
              </span>
            )}

            {item.energyLevel && (
               <span className="flex items-center gap-1 opacity-70">
                 ⚡ {item.energyLevel}
               </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
