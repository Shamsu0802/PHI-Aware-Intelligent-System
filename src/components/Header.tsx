import { useState } from "react";
import { Bell, Search, Sun, Moon, User, Activity } from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { NotificationPanel } from "@/components/NotificationPanel";

export function Header() {
  const { theme, toggle } = useTheme();
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <>
      <header className="flex h-14 items-center justify-between border-b bg-card px-4 gap-4">
        <div className="flex items-center gap-3">
          <SidebarTrigger />
          <h1 className="hidden text-sm font-semibold lg:block">
            Privacy-Aware Healthcare Communication Protection System
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-2 rounded-full bg-muted px-3 py-1 text-xs md:flex">
            <Activity className="h-3 w-3 text-success" />
            <span className="status-pulse inline-block h-2 w-2 rounded-full bg-success" />
            <span className="text-muted-foreground">System Active</span>
            <span className="text-muted-foreground">·</span>
            <span className="text-muted-foreground">Real-Time</span>
          </div>

          <div className="relative hidden md:block">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search..."
              className="h-8 w-44 rounded-full bg-muted pl-8 text-xs"
            />
          </div>

          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={toggle}>
            {theme === "light" ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
          </Button>

          <Button variant="ghost" size="icon" className="relative h-8 w-8" onClick={() => setNotifOpen(true)}>
            <Bell className="h-4 w-4" />
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-critical status-pulse" />
          </Button>

          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
            <User className="h-4 w-4" />
          </div>
        </div>
      </header>

      <NotificationPanel open={notifOpen} onClose={() => setNotifOpen(false)} />
    </>
  );
}
