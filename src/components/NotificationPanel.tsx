import { useState, useEffect, useCallback } from "react";
import { X, ShieldAlert, Ban, Eye, AlertTriangle, FileText, Volume2, VolumeX, BellRing, CheckCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAlertNotification } from "@/hooks/use-alert-notification";

const initialAlerts = [
  { id: 1, time: "Just now", title: "Patient Name detected in SMS", module: "Module 1", risk: "High", icon: ShieldAlert },
  { id: 2, time: "2 min ago", title: "Transmission blocked – MRN in email", module: "Module 2", risk: "Critical", icon: Ban },
  { id: 3, time: "5 min ago", title: "Unauthorized viewer on Screen 3", module: "Module 3", risk: "High", icon: Eye },
  { id: 4, time: "8 min ago", title: "Phone Number in WhatsApp message", module: "Module 1", risk: "Medium", icon: AlertTriangle },
  { id: 5, time: "12 min ago", title: "ECG report attachment flagged", module: "Module 2", risk: "High", icon: FileText },
  { id: 6, time: "18 min ago", title: "Mobile phone detected near display", module: "Module 3", risk: "Medium", icon: Eye },
  { id: 7, time: "25 min ago", title: "Diagnosis data in fax transmission", module: "Module 2", risk: "Critical", icon: Ban },
  { id: 8, time: "32 min ago", title: "DOB found in outgoing email", module: "Module 1", risk: "Low", icon: ShieldAlert },
];

const incomingAlerts = [
  { title: "New PHI entity in lab report upload", module: "Module 2", risk: "High", icon: FileText },
  { title: "Unknown face detected – Camera 1", module: "Module 3", risk: "Critical", icon: Eye },
  { title: "Email address in SMS channel", module: "Module 1", risk: "Medium", icon: ShieldAlert },
];

const riskClass = (r: string) => {
  switch (r) {
    case "Critical": return "bg-critical/15 text-critical border-critical/30";
    case "High": return "bg-accent/15 text-accent border-accent/30";
    case "Medium": return "bg-warning/15 text-warning border-warning/30";
    default: return "bg-success/15 text-success border-success/30";
  }
};

const riskDot = (r: string) => {
  switch (r) {
    case "Critical": return "bg-critical";
    case "High": return "bg-accent";
    case "Medium": return "bg-warning";
    default: return "bg-success";
  }
};

interface Props {
  open: boolean;
  onClose: () => void;
}

export function NotificationPanel({ open, onClose }: Props) {
  const [alerts, setAlerts] = useState(initialAlerts);
  const [nextId, setNextId] = useState(initialAlerts.length + 1);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const { notify, requestPermission } = useAlertNotification();

  // Request browser notification permission when panel opens
  useEffect(() => {
    if (open) requestPermission();
  }, [open, requestPermission]);

  // Simulate incoming alerts
  useEffect(() => {
    if (!open) return;
    let idx = 0;
    const interval = setInterval(() => {
      if (idx >= incomingAlerts.length) { idx = 0; }
      const incoming = incomingAlerts[idx];
      const newAlert = { ...incoming, id: nextId + idx, time: "Just now" };
      setAlerts((prev) => [newAlert, ...prev].slice(0, 15));
      setNextId((n) => n + 1);
      if (soundEnabled) {
        notify(incoming.title, incoming.risk);
      }
      idx++;
    }, 6000);
    return () => clearInterval(interval);
  }, [open, nextId, soundEnabled, notify]);

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div className="fixed inset-0 z-40 bg-foreground/10 backdrop-blur-[2px]" onClick={onClose} />
      )}

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 z-50 h-full w-full max-w-sm bg-card border-l shadow-2xl transition-transform duration-300 ease-out ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center justify-between border-b px-4">
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">Privacy Alerts</h2>
            <Badge variant="outline" className="bg-critical/15 text-critical border-critical/30 text-[10px]">
              {alerts.length} active
            </Badge>
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={() => setSoundEnabled(!soundEnabled)}
              title={soundEnabled ? "Mute alerts" : "Unmute alerts"}
            >
              {soundEnabled ? <Volume2 className="h-4 w-4 text-primary" /> : <VolumeX className="h-4 w-4 text-muted-foreground" />}
            </Button>
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {alerts.length > 0 && (
          <div className="flex items-center justify-between border-b px-4 py-2">
            <span className="text-[11px] text-muted-foreground">{alerts.length} unread</span>
            <Button variant="ghost" size="sm" className="h-7 text-xs gap-1.5" onClick={() => setAlerts([])}>
              <CheckCheck className="h-3.5 w-3.5" /> Mark all as read
            </Button>
          </div>
        )}

        <ScrollArea className="h-[calc(100%-3.5rem-2.5rem)]">
          <div className="p-3 space-y-2">
            {alerts.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                <CheckCheck className="h-8 w-8 mb-2 opacity-40" />
                <p className="text-sm">All caught up!</p>
              </div>
            )}
            {alerts.map((alert, i) => (
              <div
                key={`${alert.id}-${i}`}
                className={`group relative rounded-lg border bg-card p-3 space-y-2 transition-all duration-300 hover:bg-muted/30 ${
                  i === 0 ? "animate-fade-in" : ""
                }`}
              >
                <button
                  onClick={() => setAlerts((prev) => prev.filter((_, idx) => idx !== i))}
                  className="absolute right-2 top-2 hidden h-5 w-5 items-center justify-center rounded-full bg-muted text-muted-foreground hover:bg-destructive/15 hover:text-destructive group-hover:flex transition-colors"
                  title="Dismiss"
                >
                  <X className="h-3 w-3" />
                </button>
                <div className="flex items-start gap-2.5">
                  <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md ${riskClass(alert.risk)}`}>
                    <alert.icon className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium leading-snug">{alert.title}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className={`status-pulse h-1.5 w-1.5 rounded-full ${riskDot(alert.risk)}`} />
                      <Badge variant="outline" className={`${riskClass(alert.risk)} text-[10px] px-1.5 py-0`}>
                        {alert.risk}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">{alert.module}</span>
                      <span className="ml-auto text-[10px] text-muted-foreground font-mono">{alert.time}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </>
  );
}
