import { useItems, useUpdateItem, useCreateItem } from "@/hooks/use-items";
import { useProjects, useCreateProject } from "@/hooks/use-projects";
import { ItemRow } from "@/components/item-row";
import { ItemDialog, ProjectDialog } from "@/components/item-dialog";
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
  arrayMove,
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
  Zap,
  Plus
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  ContextMenu, 
  ContextMenuContent, 
  ContextMenuItem, 
  ContextMenuTrigger 
} from "@/components/ui/context-menu";

interface BinProps {
  id: string;
  title: string;
  icon: any;
  children?: React.ReactNode;
  canDrop?: boolean;
  className?: string;
}

function Bin({ id, title, icon: Icon, children, canDrop = true, className }: BinProps) {
  const { setNodeRef } = useDroppable({ id, disabled: !canDrop });

  return (
    <div ref={setNodeRef} className={`flex flex-col h-[400px] bg-card border rounded-xl overflow-hidden shadow-sm ${className}`}>
      <div className="p-3 border-b bg-muted/30 flex items-center justify-between">
        <div className="flex items-center gap-2 font-semibold text-sm">
          <Icon className="w-4 h-4 text-primary" />
          {title}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {children}
      </div>
    </div>
  );
}

function ProjectPane({ project, items, onEdit, onEditProject }: { project: Project, items: Item[], onEdit: (item: Item) => void, onEditProject: (project: Project) => void }) {
  const { setNodeRef } = useDroppable({ id: `project-${project.id}` });

  return (
    <div ref={setNodeRef} className="border rounded-lg bg-muted/20 p-2 space-y-1">
      <div 
        className="text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1 px-1 cursor-pointer hover:text-primary transition-colors"
        onClick={() => onEditProject(project)}
      >
        {project.name}
      </div>
      <SortableContext items={items.map(i => i.id)} strategy={verticalListSortingStrategy}>
        {items.map((item) => (
          <SortableItem key={item.id} item={item} onEdit={onEdit} />
        ))}
      </SortableContext>
      {items.length === 0 && (
        <div className="text-[10px] text-center py-2 text-muted-foreground/50 italic">Empty Project</div>
      )}
    </div>
  );
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

export default function DashboardPage() {
  const { data: items = [], isLoading: itemsLoading } = useItems();
  const { data: projects = [], isLoading: projectsLoading } = useProjects();
  const updateItem = useUpdateItem();
  const createItem = useCreateItem();
  const { mutateAsync: createProject } = useCreateProject();
  
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [showProjectDialog, setShowProjectDialog] = useState(false);

  const handleEditProject = (project: Project) => {
    setSelectedProject(project);
    setShowProjectDialog(true);
  };

  const handleNewProject = () => {
    setSelectedProject(null);
    setShowProjectDialog(true);
  };
  
  // Quick capture state
  const [quickTitle, setQuickTitle] = useState("");
  const [quickDate, setQuickDate] = useState("");
  const [quickTime, setQuickTime] = useState("");

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  if (itemsLoading || projectsLoading) {
    return <div className="p-8 text-muted-foreground font-sans">Loading dashboard...</div>;
  }

  const handleQuickCapture = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickTitle.trim()) return;
    
    await createItem.mutateAsync({
      title: quickTitle,
      status: "inbox",
      dueDatetime: quickDate ? new Date(quickDate) : null,
      startTime: quickTime || null,
    });
    
    setQuickTitle("");
    setQuickDate("");
    setQuickTime("");
  };

  const getInboxItems = () => items.filter(i => i.status === "inbox" || (i.status === "done" && !i.projectId));
  const getSomedayItems = () => items.filter(i => i.status === "someday");
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
        .filter(i => i.projectId === project.id && (i.status === "projects" || i.status === "done"))
        .sort((a, b) => (a.position || 0) - (b.position || 0));
      if (projectItems.length > 0) {
        // Show first non-done item, or if all are done, maybe show the first done one?
        // GTD says Next Action is the very first one.
        nextActions.push(projectItems[0]);
      }
    });
    return nextActions;
  };

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as number);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveId(null);
    if (!over) return;

    const activeId = active.id as number;
    const overId = over.id; 
    
    // 1. Dropping onto a project pane
    if (typeof overId === "string" && overId.startsWith("project-")) {
      const projectId = parseInt(overId.replace("project-", ""));
      const projectItems = items.filter(i => i.projectId === projectId).sort((a,b) => (a.position || 0) - (b.position || 0));
      const maxPos = projectItems.length > 0 ? Math.max(...projectItems.map(i => i.position || 0)) : -1;
      await updateItem.mutateAsync({ id: activeId, status: "projects", projectId, position: maxPos + 1 });
      return;
    }

    // 2. Dropping onto an item
    const overIdNum = Number(overId);
    const overItem = items.find(i => i.id === overIdNum);
    const activeItem = items.find(i => i.id === activeId);

    if (overItem && activeItem) {
      // Reordering within the same project
      if (overItem.projectId && activeItem.projectId === overItem.projectId) {
        const projectId = overItem.projectId;
        const projectItems = items
          .filter(i => i.projectId === projectId)
          .sort((a, b) => (a.position || 0) - (b.position || 0));
          
        const oldIndex = projectItems.findIndex(i => i.id === activeId);
        const newIndex = projectItems.findIndex(i => i.id === overIdNum);
        
        if (oldIndex !== -1 && newIndex !== -1) {
          const newOrder = arrayMove(projectItems, oldIndex, newIndex);
          // Sequential updates to avoid race conditions and ensure visual sync
          for (let i = 0; i < newOrder.length; i++) {
            await updateItem.mutateAsync({ 
              id: newOrder[i].id, 
              position: i,
              status: "projects",
              projectId: projectId
            });
          }
        }
      } 
      // Moving to a different project by dropping on its item
      else if (overItem.projectId) {
        await updateItem.mutateAsync({ 
          id: activeId, 
          status: "projects", 
          projectId: overItem.projectId,
          position: (overItem.position || 0)
        });
      }
      return;
    }

    // 3. Drop into bins
    if (typeof overId === "string" && ["inbox", "someday"].includes(overId)) {
      await updateItem.mutateAsync({ id: activeId, status: overId, projectId: null, position: 0 });
    }
  };

  const activeItem = items.find(i => i.id === activeId);

  return (
    <div className="h-full flex flex-col gap-6 p-6 font-sans overflow-hidden">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight uppercase">GTD</h1>
      </header>

      <DndContext 
        sensors={sensors}
        collisionDetection={closestCorners}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        <div className="flex flex-col gap-6 flex-1 min-h-0 overflow-y-auto pr-2">
          {/* TOP ROW: Bins */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* INBOX */}
            <Bin id="inbox" title="Inbox" icon={Inbox}>
              <form onSubmit={handleQuickCapture} className="space-y-2 mb-4 bg-muted/30 p-2 rounded-lg border">
                <Input 
                  value={quickTitle} 
                  onChange={e => setQuickTitle(e.target.value)} 
                  placeholder="Quick capture..." 
                  className="h-8 text-xs font-sans"
                />
                <div className="flex gap-1">
                  <Input 
                    type="date" 
                    value={quickDate} 
                    onChange={e => setQuickDate(e.target.value)} 
                    className="h-7 text-[10px] p-1 font-sans"
                  />
                  <Input 
                    type="time" 
                    value={quickTime} 
                    onChange={e => setQuickTime(e.target.value)} 
                    className="h-7 text-[10px] p-1 font-sans"
                  />
                </div>
                <Button type="submit" size="sm" className="w-full h-7 text-xs">Add</Button>
              </form>
              <SortableContext items={getInboxItems().map(i => i.id)} strategy={verticalListSortingStrategy}>
                {getInboxItems().map(item => (
                  <SortableItem key={item.id} item={item} onEdit={setSelectedItem} />
                ))}
              </SortableContext>
            </Bin>

            {/* CALENDAR */}
            <Bin id="calendar" title="Calendar" icon={CalendarIcon} canDrop={false}>
              {getCalendarItems().map(item => (
                <ItemRow key={item.id} item={item} onEdit={setSelectedItem} />
              ))}
            </Bin>

            {/* NEXT ACTIONS */}
            <Bin id="next" title="Next Actions" icon={Zap} canDrop={false}>
              {getNextActions().map(item => (
                <ItemRow key={item.id} item={item} />
              ))}
            </Bin>

            {/* SOMEDAY */}
            <Bin id="someday" title="Someday" icon={Archive}>
              <SortableContext items={getSomedayItems().map(i => i.id)} strategy={verticalListSortingStrategy}>
                {getSomedayItems().map(item => (
                  <SortableItem key={item.id} item={item} onEdit={setSelectedItem} />
                ))}
              </SortableContext>
            </Bin>
          </div>

          {/* BOTTOM ROW: Projects */}
          <div className="flex-1 min-h-[400px]">
            <ContextMenu>
              <ContextMenuTrigger className="flex flex-col h-full">
                <Bin id="projects" title="Projects" icon={Layers} canDrop={false} className="h-full">
                  <div className="flex flex-row gap-4 h-full overflow-x-auto pb-2">
                    {projects.map(project => (
                      <div key={project.id} className="min-w-[300px] flex-shrink-0 h-fit">
                        <ProjectPane 
                          project={project} 
                          items={items
                            .filter(i => i.projectId === project.id && (i.status === "projects" || i.status === "done"))
                            .sort((a, b) => (a.position || 0) - (b.position || 0))
                          } 
                          onEdit={setSelectedItem}
                          onEditProject={handleEditProject}
                        />
                      </div>
                    ))}
                    {projects.length === 0 && (
                      <div className="h-full w-full flex flex-col items-center justify-center text-muted-foreground/30 text-xs italic">
                        <p>No projects</p>
                        <p className="text-[10px] mt-1">Right-click to create</p>
                      </div>
                    )}
                  </div>
                </Bin>
              </ContextMenuTrigger>
              <ContextMenuContent>
                <ContextMenuItem onClick={handleNewProject}>
                  <Plus className="w-4 h-4 mr-2" /> New Project
                </ContextMenuItem>
              </ContextMenuContent>
            </ContextMenu>
          </div>
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

      <ProjectDialog 
        project={selectedProject}
        open={showProjectDialog} 
        onClose={() => setShowProjectDialog(false)} 
      />
    </div>
  );
}
