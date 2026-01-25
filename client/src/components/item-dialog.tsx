import { Item, Project } from "@shared/schema";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState, useEffect } from "react";
import { useUpdateItem, useDeleteItem } from "@/hooks/use-items";
import { useProjects, useCreateProject } from "@/hooks/use-projects";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface ItemDialogProps {
  item: Item | null;
  open: boolean;
  onClose: () => void;
}

export function ItemDialog({ item, open, onClose }: ItemDialogProps) {
  const updateItem = useUpdateItem();
  const deleteItem = useDeleteItem();
  const { data: projects } = useProjects();
  
  const [formData, setFormData] = useState<Partial<Item>>({});

  useEffect(() => {
    if (item) {
      setFormData(item);
    }
  }, [item]);

  const handleSave = async () => {
    if (!item) return;
    await updateItem.mutateAsync({
      id: item.id,
      ...formData,
    });
    onClose();
  };

  const handleDelete = async () => {
    if (!item) return;
    await deleteItem.mutateAsync(item.id);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md font-sans">
        <DialogHeader>
          <DialogTitle>Item Details</DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="title">Task Name</Label>
            <Input 
              id="title" 
              value={formData.title || ""} 
              onChange={e => setFormData({...formData, title: e.target.value})} 
              placeholder="What needs to be done?"
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label>Date</Label>
              <Input 
                type="date"
                value={formData.dueDatetime ? new Date(formData.dueDatetime).toISOString().split('T')[0] : ""}
                onChange={e => setFormData({...formData, dueDatetime: e.target.value ? new Date(e.target.value) : null})}
              />
            </div>
            <div className="grid gap-2">
              <Label>Start Time</Label>
              <Input 
                type="time"
                value={formData.startTime || ""}
                onChange={e => setFormData({...formData, startTime: e.target.value})}
              />
            </div>
          </div>

          <div className="grid gap-2">
            <Label>Project</Label>
            <Select 
              value={formData.projectId?.toString() || "none"} 
              onValueChange={val => setFormData({...formData, projectId: val === "none" ? null : Number(val)})}
            >
              <SelectTrigger><SelectValue placeholder="No Project" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">No Project</SelectItem>
                {projects?.map(p => (
                  <SelectItem key={p.id} value={p.id.toString()}>{p.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter className="flex justify-between sm:justify-between w-full">
          <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleSave}>Save</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ProjectDialog({ project, open, onClose }: { project?: Project | null, open: boolean, onClose: () => void }) {
  const [name, setName] = useState("");
  const createProject = useCreateProject();
  const updateProject = useUpdateProject();

  useEffect(() => {
    if (project) {
      setName(project.name);
    } else {
      setName("");
    }
  }, [project, open]);

  const handleSave = async () => {
    if (!name.trim()) return;
    if (project) {
      await updateProject.mutateAsync({ id: project.id, name });
    } else {
      await createProject.mutateAsync({ name });
    }
    setName("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md font-sans">
        <DialogHeader><DialogTitle>{project ? "Edit Project" : "New Project"}</DialogTitle></DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label>Project Name</Label>
            <Input value={name} onChange={e => setName(e.target.value)} placeholder="Name your project..." />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave}>{project ? "Save" : "Create"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
