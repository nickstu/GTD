import { Item, Project } from "@shared/schema";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useEffect } from "react";
import { useUpdateItem, useDeleteItem } from "@/hooks/use-items";
import { useProjects } from "@/hooks/use-projects";
import { format } from "date-fns";

interface ItemDialogProps {
  item: Item | null;
  open: boolean;
  onClose: () => void;
  mode?: "edit" | "process";
}

export function ItemDialog({ item, open, onClose, mode = "edit" }: ItemDialogProps) {
  const updateItem = useUpdateItem();
  const deleteItem = useDeleteItem();
  const { data: projects } = useProjects();
  
  const [formData, setFormData] = useState<Partial<Item>>({});
  const [step, setStep] = useState<"clarify" | "organize">("clarify");

  useEffect(() => {
    if (item) {
      setFormData(item);
      setStep(mode === "process" ? "clarify" : "organize");
    }
  }, [item, mode]);

  const handleSave = async (statusOverride?: string) => {
    if (!item) return;
    
    const status = statusOverride || formData.status || item.status;
    
    await updateItem.mutateAsync({
      id: item.id,
      ...formData,
      status
    });
    onClose();
  };

  const handleDelete = async () => {
    if (!item) return;
    await deleteItem.mutateAsync(item.id);
    onClose();
  };

  const isProcessing = mode === "process";

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isProcessing && step === "clarify" ? "Clarify Item" : "Item Details"}
          </DialogTitle>
        </DialogHeader>

        {/* PROCESSING FLOW - STEP 1: CLARIFY */}
        {isProcessing && step === "clarify" ? (
          <div className="space-y-6 py-4">
            <div className="p-4 bg-muted/50 rounded-lg text-lg font-medium text-center">
              "{item?.title}"
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider text-center">Not Actionable?</h3>
                <div className="grid gap-2">
                  <Button variant="outline" onClick={() => handleDelete()} className="justify-start gap-2 hover:bg-destructive/10 hover:text-destructive">
                    🗑️ Trash
                  </Button>
                  <Button variant="outline" onClick={() => handleSave("someday")} className="justify-start gap-2">
                    📦 Someday/Maybe
                  </Button>
                  <Button variant="outline" onClick={() => handleSave("reference")} className="justify-start gap-2">
                    📚 Reference
                  </Button>
                </div>
              </div>
              
              <div className="space-y-4 border-l pl-4">
                <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wider text-center">Actionable?</h3>
                <div className="grid gap-2">
                  <Button onClick={() => setStep("organize")} className="justify-start gap-2 bg-primary/10 text-primary hover:bg-primary/20 border-primary/20">
                    ⚡ Next Action
                  </Button>
                  <Button variant="secondary" onClick={() => handleSave("waiting")} className="justify-start gap-2">
                    ⏳ Waiting For
                  </Button>
                </div>
              </div>
            </div>
            
            <div className="text-center text-sm text-muted-foreground pt-4 border-t">
              Does it take less than 2 minutes? <span className="font-bold text-foreground">Do it now!</span>
            </div>
            <Button variant="ghost" className="w-full" onClick={() => handleSave("done")}>Mark as Done</Button>
          </div>
        ) : (
          /* EDIT / ORGANIZE FORM */
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="title">Title (Next Action Verb)</Label>
              <Input 
                id="title" 
                value={formData.title || ""} 
                onChange={e => setFormData({...formData, title: e.target.value})} 
                placeholder="e.g. Call Mom about..."
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
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

              <div className="grid gap-2">
                <Label>Context (@tag)</Label>
                <Input 
                  placeholder="@calls, @home"
                  value={formData.contexts?.join(", ") || ""}
                  onChange={e => setFormData({...formData, contexts: e.target.value.split(",").map(s => s.trim()).filter(Boolean)})}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="grid gap-2">
                <Label>Time Estimate</Label>
                <Input 
                  placeholder="15m"
                  value={formData.timeEstimate || ""}
                  onChange={e => setFormData({...formData, timeEstimate: e.target.value})}
                />
              </div>
              
              <div className="grid gap-2">
                <Label>Energy</Label>
                <Select 
                  value={formData.energyLevel || "none"} 
                  onValueChange={val => setFormData({...formData, energyLevel: val === "none" ? null : val})}
                >
                  <SelectTrigger><SelectValue placeholder="Any" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Any</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label>List</Label>
                <Select 
                  value={formData.status || "inbox"} 
                  onValueChange={val => setFormData({...formData, status: val})}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="inbox">Inbox</SelectItem>
                    <SelectItem value="next">Next Actions</SelectItem>
                    <SelectItem value="waiting">Waiting For</SelectItem>
                    <SelectItem value="someday">Someday/Maybe</SelectItem>
                    <SelectItem value="reference">Reference</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="grid gap-2">
              <Label>Due Date (Calendar Only)</Label>
              <Input 
                type="datetime-local"
                value={formData.dueDatetime ? new Date(formData.dueDatetime).toISOString().slice(0, 16) : ""}
                onChange={e => setFormData({...formData, dueDatetime: e.target.value ? new Date(e.target.value) : null})}
              />
            </div>

            <div className="grid gap-2">
              <Label>Notes</Label>
              <Textarea 
                value={formData.notes || ""}
                onChange={e => setFormData({...formData, notes: e.target.value})}
                placeholder="Details, reference info..."
                className="h-24"
              />
            </div>
            
            <DialogFooter className="gap-2 sm:gap-0">
              <Button variant="destructive" type="button" onClick={handleDelete} className="mr-auto">Delete</Button>
              <Button variant="outline" type="button" onClick={onClose}>Cancel</Button>
              <Button type="button" onClick={() => handleSave()}>Save Changes</Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
