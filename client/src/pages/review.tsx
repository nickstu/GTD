import { useItems } from "@/hooks/use-items";
import { useProjects } from "@/hooks/use-projects";
import { Link } from "wouter";
import { CheckCircle2, Inbox, AlertTriangle, ListChecks } from "lucide-react";

export default function ReviewPage() {
  const { data: items } = useItems();
  const { data: projects } = useProjects();

  const inboxCount = items?.filter(i => i.status === "inbox").length || 0;
  const activeProjects = projects?.filter(p => p.status === "active") || [];
  
  const stuckProjects = activeProjects.filter(project => {
    const projectItems = items?.filter(i => i.projectId === project.id && i.status !== "done") || [];
    return !projectItems.some(i => i.status === "next");
  });

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="text-center space-y-2 mb-12">
        <h1 className="text-4xl font-bold tracking-tight">Weekly Review</h1>
        <p className="text-lg text-muted-foreground">Clear your mind. Get current.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-card border rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center gap-4 mb-4">
            <div className="p-3 bg-blue-100 text-blue-600 rounded-xl">
              <Inbox className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-lg">Inbox</h3>
              <p className="text-muted-foreground text-sm">Get to zero</p>
            </div>
            <div className="ml-auto text-2xl font-bold">{inboxCount}</div>
          </div>
          <Link href="/inbox" className="text-sm font-medium text-primary hover:underline">Process Inbox &rarr;</Link>
        </div>

        <div className="bg-card border rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center gap-4 mb-4">
             <div className="p-3 bg-amber-100 text-amber-600 rounded-xl">
               <AlertTriangle className="w-6 h-6" />
             </div>
             <div>
               <h3 className="font-bold text-lg">Stuck Projects</h3>
               <p className="text-muted-foreground text-sm">Missing next actions</p>
             </div>
             <div className="ml-auto text-2xl font-bold">{stuckProjects.length}</div>
          </div>
          <Link href="/projects" className="text-sm font-medium text-primary hover:underline">Review Projects &rarr;</Link>
        </div>
      </div>

      <div className="bg-card border rounded-2xl overflow-hidden shadow-sm">
        <div className="p-6 border-b bg-muted/30">
          <h3 className="font-bold text-lg flex items-center gap-2">
            <ListChecks className="w-5 h-5" />
            Review Checklist
          </h3>
        </div>
        <div className="divide-y">
          {[
            "Empty your head (Quick Capture)",
            "Process Inbox to zero",
            "Review 'Next Actions' list",
            "Review 'Waiting For' list",
            "Review 'Someday/Maybe' list",
            "Review upcoming calendar",
            "Review Projects (ensure each has a next action)"
          ].map((step, i) => (
            <label key={i} className="flex items-center gap-4 p-4 hover:bg-muted/50 cursor-pointer transition-colors">
              <input type="checkbox" className="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary" />
              <span className="font-medium">{step}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
