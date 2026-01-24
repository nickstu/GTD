import { Switch, Route, Redirect } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import { LayoutShell } from "@/components/layout-shell";

// Pages
import DashboardPage from "@/pages/dashboard";
import InboxPage from "@/pages/inbox";
import NextActionsPage from "@/pages/next-actions";
import ProjectsPage from "@/pages/projects";
import WaitingForPage from "@/pages/waiting-for";
import CalendarPage from "@/pages/calendar";
import ReviewPage from "@/pages/review";
import ReferencePage from "@/pages/reference";
import SomedayPage from "@/pages/someday";

function Router() {
  return (
    <LayoutShell>
      <Switch>
        <Route path="/" component={DashboardPage} />
        <Route path="/inbox" component={InboxPage} />
        <Route path="/next-actions" component={NextActionsPage} />
        <Route path="/projects" component={ProjectsPage} />
        <Route path="/waiting-for" component={WaitingForPage} />
        <Route path="/calendar" component={CalendarPage} />
        <Route path="/review" component={ReviewPage} />
        <Route path="/reference" component={ReferencePage} />
        <Route path="/someday" component={SomedayPage} />
        
        <Route component={NotFound} />
      </Switch>
    </LayoutShell>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
