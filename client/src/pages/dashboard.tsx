import { useItems, useUpdateItem } from "@/hooks/use-items";
import { useProjects } from "@/hooks/use-projects";
import { ItemRow } from "@/components/item-row";
import { ItemDialog } from "@/components/item-dialog";
import { useState } from "react";
import { Item, Project } from "@shared/schema";
import { 
  DndContext, 
  DragOverlay, 
  closestCorners, 
  KeyboardSensor, 
  PointerSensor, 
  useSensor, 
  useSensors,
  DragStartEvent,
  DragEndEvent,
  useDroppable
} from "@dnd-kit/core";
import { 
  SortableContext, 
  sortableKeyboardCoordinates, 
  verticalListSortingStrategy,
  useSortable
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { 
  Inbox, 
  Layers, 
  Archive, 
  Calendar as CalendarIcon, 
  Zap 
} from "lucide-react";
import { format } from "date-fns";

interface BinProps {
  id: string;
  title: string;
  icon: any;
  items: Item[];
  onEdit?: (item: Item) => void;
  canDrop?: boolean;
}

function SortableItem({ item, onEdit }: { item: Item; onEdit?: (item: Item) => void }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: item.id, disabled: !onEdit });

  const style = {
    transform: CSS.Translate.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <ItemRow item={item} onEdit={onEdit} />
    </div>
  );
}

function Bin({ id, title, icon: Icon, items, onEdit, canDrop = true }: BinProps) {
  const { setNodeRef } = useDroppable({ id, disabled: !canDrop });

  return (
    <div ref={setNodeRef} className="flex flex-col h-[400px] bg-card border rounded-xl overflow-hidden shadow-sm">
      <div className="p-3 border-b bg-muted/30 flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-sm">
          <Icon className="w-4 h-4 text-primary" />
          {title}
        </div>
        <span className="text-xs text-muted-foreground bg-background px-1.5 py-0.5 rounded border">
          {items.length}
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <SortableContext items={items.map(i => i.id)} strategy={verticalListSortingStrategy}>
          {items.map((item) => (
            <SortableItem key={item.id} item={item} onEdit={onEdit} />
          ))}
        </SortableContext>
        {items.length === 0 && (
          <div className="h-full flex items-center justify-center text-muted-foreground/30 text-xs italic">
            Empty
          </div>
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: items = [], isLoading: itemsLoading } = useItems();
  const { data: projects = [], isLoading: projectsLoading } = useProjects();
  const updateItem = useUpdateItem();
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  if (itemsLoading || projectsLoading) {
    return <div className="p-8 text-muted-foreground font-sans">Loading dashboard...</div>;
  }

  const getInboxItems = () => items.filter(i => i.status === "inbox");
  const getSomedayItems = () => items.filter(i => i.status === "someday");
  const getProjectItems = () => items.filter(i => i.status === "projects");
  const getCalendarItems = () => {
    return items
      .filter(i => i.dueDatetime)
      .sort((a, b) => {
        const dateA = new Date(a.dueDatetime!).getTime();
        const dateB = new Date(b.dueDatetime!).getTime();
        if (dateA !== dateB) return dateA - dateB;
        return (a.startTime || "").localeCompare(b.startTime || "");
      });
  };

  const getNextActions = () => {
    const nextActions: Item[] = [];
    projects.forEach(project => {
      const projectItems = items
        .filter(i => i.projectId === project.id && i.status === "projects")
        .sort((a, b) => (a.position || 0) - (b.position || 0));
      if (projectItems.length > 0) {
        nextActions.push(projectItems[0]);
      }
    });
    return nextActions;
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as number);
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const itemId = active.id as number;
    const overId = over.id as string;
    const item = items.find(i => i.id === itemId);
    if (!item) return;

    // Disallow dropping into next actions
    if (overId === "next") return;

    // Handle drops into bins
    if (["inbox", "someday", "projects"].includes(overId)) {
      updateItem.mutate({ id: itemId, status: overId });
    }
  };

  const activeItem = items.find(i => i.id === activeId);

  return (
    <div className="h-full flex flex-col gap-6 p-6 font-sans">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">GTD BINS</h1>
      </header>

      <DndContext 
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 flex-1">
          <Bin id="inbox" title="Inbox" icon={Inbox} items={getInboxItems()} onEdit={setSelectedItem} />
          <Bin id="next" title="Next Actions" icon={Zap} items={getNextActions()} canDrop={false} />
          <Bin id="projects" title="Projects" icon={Layers} items={getProjectItems()} onEdit={setSelectedItem} />
          <Bin id="someday" title="Someday" icon={Archive} items={getSomedayItems()} onEdit={setSelectedItem} />
          <Bin id="calendar" title="Calendar" icon={CalendarIcon} items={getCalendarItems()} onEdit={setSelectedItem} />
        </div>

        <DragOverlay>
          {activeItem ? (
            <div className="bg-card border rounded shadow-xl p-2 opacity-80 scale-105 pointer-events-none font-sans">
              <ItemRow item={activeItem} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      <ItemDialog 
        item={selectedItem} 
        open={!!selectedItem} 
        onClose={() => setSelectedItem(null)} 
      />
    </div>
  );
}
