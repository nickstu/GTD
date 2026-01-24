import { Link, useLocation } from "wouter";
import { 
  Inbox, 
  CheckSquare, 
  Layers, 
  Clock, 
  Archive, 
  BookOpen, 
  Calendar, 
  BarChart3,
  Plus,
  Search,
  Settings
} from "lucide-react";
import { useState, useEffect } from "react";
import { useCreateItem } from "@/hooks/use-items";
import { useItems } from "@/hooks/use-items";

const navItems = [
  { href: "/", icon: Layers, label: "Dashboard", shortcut: "d" },
  { href: "/inbox", icon: Inbox, label: "Inbox", shortcut: "i" },
  { href: "/next-actions", icon: CheckSquare, label: "Next Actions", shortcut: "n" },
  { href: "/projects", icon: Layers, label: "Projects", shortcut: "p" },
  { href: "/waiting-for", icon: Clock, label: "Waiting For", shortcut: "w" },
  { href: "/calendar", icon: Calendar, label: "Calendar", shortcut: "c" },
  { href: "/someday", icon: Archive, label: "Someday/Maybe", shortcut: "s" },
  { href: "/reference", icon: BookOpen, label: "Reference", shortcut: "r" },
  { href: "/review", icon: BarChart3, label: "Review", shortcut: "v" },
];

export function LayoutShell({ children }: { children: React.ReactNode }) {
  const [quickAddOpen, setQuickAddOpen] = useState(false);
  const [quickAddText, setQuickAddText] = useState("");
  const createItem = useCreateItem();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      
      if (e.key === "q" || e.key === "c") {
        e.preventDefault();
        setQuickAddOpen(true);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleQuickAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickAddText.trim()) return;
    
    await createItem.mutateAsync({
      title: quickAddText,
      status: "inbox",
    });
    
    setQuickAddText("");
    setQuickAddOpen(false);
  };

  return (
    <div className="flex h-screen bg-background overflow-hidden font-sans">
      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        <div className="flex-1 overflow-y-auto w-full">
          {children}
        </div>
      </main>

      {/* Quick Capture Modal Overlay */}
      {quickAddOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-[20vh] px-4">
          <div className="bg-card w-full max-w-lg rounded-xl shadow-2xl border p-1 animate-in fade-in zoom-in-95 duration-200">
            <form onSubmit={handleQuickAdd}>
              <input
                autoFocus
                type="text"
                placeholder="What's on your mind?"
                className="w-full px-4 py-4 text-lg bg-transparent border-none outline-none placeholder:text-muted-foreground/50 font-sans"
                value={quickAddText}
                onChange={(e) => setQuickAddText(e.target.value)}
                onBlur={() => !quickAddText && setQuickAddOpen(false)}
                onKeyDown={(e) => {
                  if (e.key === "Escape") setQuickAddOpen(false);
                }}
              />
              <div className="px-4 py-2 flex justify-between items-center border-t bg-muted/30 text-xs text-muted-foreground rounded-b-lg font-sans">
                <span>Capture to Inbox</span>
                <div className="flex gap-2">
                  <span className="bg-background border px-1.5 py-0.5 rounded shadow-sm">Enter</span> to save
                  <span className="bg-background border px-1.5 py-0.5 rounded shadow-sm">Esc</span> to cancel
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
