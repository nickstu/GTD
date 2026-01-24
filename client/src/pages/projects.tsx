import { useProjects, useCreateProject } from "@/hooks/use-projects";
import { useItems } from "@/hooks/use-items";
import { useState } from "react";
import { Plus, AlertTriangle, ChevronRight, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ItemRow } from "@/components/item-row";
import { Project, Item } from "@shared/schema";

export default function ProjectsPage() {
  const { data: projects } = useProjects();
  const { data: items } = useItems();
  const createProject = useCreateProject();
  
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newProject, setNewProject] = useState({ name: "", outcome: "" });
  const [expandedProjects, setExpandedProjects] = useState<Set<number>>(new Set());

  const activeProjects = projects?.filter(p => p.status === "active") || [];

  const handleCreate = async () => {
    await createProject.mutateAsync(newProject);
    setIsCreateOpen(false);
    setNewProject({ name: "", outcome: "" });
  };

  const toggleExpand = (id: number) => {
    const next = new Set(expandedProjects);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedProjects(next);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
        <Button onClick={() => setIsCreateOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" /> New Project
        </Button>
      </div>

      <div className="grid gap-4">
        {activeProjects.map(project => {
          const projectItems = items?.filter(i => i.projectId === project.id && i.status !== "done") || [];
          const hasNextAction = projectItems.some(i => i.status === "next");
          const isExpanded = expandedProjects.has(project.id);

          return (
            <div key={project.id} className="bg-card border rounded-xl shadow-sm overflow-hidden">
              <div 
                className="p-4 flex items-center justify-between cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => toggleExpand(project.id)}
              >
                <div className="flex items-center gap-3">
                  <div className="text-muted-foreground">
                    {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg">{project.name}</h3>
                    {project.outcome && <p className="text-sm text-muted-foreground">{project.outcome}</p>}
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  {!hasNextAction && (
                    <div className="flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-1 rounded text-xs font-medium border border-amber-100">
                      <AlertTriangle className="w-3 h-3" /> Needs Action
                    </div>
                  )}
                  <div className="text-sm font-medium text-muted-foreground bg-muted px-2 py-1 rounded">
                    {projectItems.length} active
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="border-t bg-muted/10 p-2 space-y-1">
                   {projectItems.length === 0 ? (
                     <div className="p-4 text-center text-sm text-muted-foreground italic">No active items. Add a next action.</div>
                   ) : (
                     projectItems.map(item => (
                       <ItemRow key={item.id} item={item} showStatus />
                     ))
                   )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Create Project Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>New Project</DialogTitle></DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Project Name</Label>
              <Input 
                value={newProject.name} 
                onChange={e => setNewProject({...newProject, name: e.target.value})} 
                placeholder="e.g. Summer Vacation"
              />
            </div>
            <div className="space-y-2">
              <Label>Outcome (Definition of Done)</Label>
              <Textarea 
                value={newProject.outcome} 
                onChange={e => setNewProject({...newProject, outcome: e.target.value})} 
                placeholder="What does success look like?"
              />
            </div>
            <Button onClick={handleCreate} disabled={!newProject.name} className="w-full">Create Project</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
