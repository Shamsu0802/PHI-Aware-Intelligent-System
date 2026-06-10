import { useState, useEffect } from "react";
import { format, parseISO, isWithinInterval, startOfDay, endOfDay } from "date-fns";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  FileText,
  Search,
  Download,
  CalendarIcon,
  X,
} from "lucide-react";
import { downloadCSV, downloadPDF } from "@/lib/export-utils";
import { cn } from "@/lib/utils";
import type { DateRange } from "react-day-picker";

const riskClass = (r: string) => {
  switch (r) {
    case "Critical":
      return "bg-critical/15 text-critical border-critical/30";
    case "High":
      return "bg-accent/15 text-accent border-accent/30";
    case "Medium":
      return "bg-warning/15 text-warning border-warning/30";
    default:
      return "bg-success/15 text-success border-success/30";
  }
};

export default function IncidentLogs() {
  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [moduleFilter, setModuleFilter] = useState("all");
  const [dateRange, setDateRange] = useState<DateRange | undefined>(undefined);

  const [incidents, setIncidents] = useState<any[]>([]);

  useEffect(() => {
    const loadIncidents = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/dashboard/incidents"
        );
        const data = await response.json();

        setIncidents(
          data.map((item: any) => ({
            time: item.time,
            user:
              item.module === "Module 1"
                ? "Analyzer"
                : item.module === "Module 2"
                ? "Secure Communication"
                : "Screen Privacy",
            module: item.module,
            event: item.event,
            phi: item.phi,
            risk: item.risk,
            action: item.action,
          }))
        );
      } catch (error) {
        console.error("Failed to fetch incident logs:", error);
      }
    };

    loadIncidents();

    const interval = setInterval(loadIncidents, 3000);

    return () => clearInterval(interval);
  }, []);

  const filtered = incidents.filter((i) => {
    const matchSearch =
      !search ||
      Object.values(i).some((v) =>
        String(v).toLowerCase().includes(search.toLowerCase())
      );

    const matchRisk = riskFilter === "all" || i.risk === riskFilter;
    const matchModule =
      moduleFilter === "all" || i.module === moduleFilter;

    const matchDate =
      !dateRange?.from ||
      isWithinInterval(parseISO(i.time.replace(" ", "T")), {
        start: startOfDay(dateRange.from),
        end: endOfDay(dateRange.to ?? dateRange.from),
      });

    return matchSearch && matchRisk && matchModule && matchDate;
  });

  const logHeaders = [
    "Timestamp",
    "User",
    "Module",
    "Event Type",
    "Detected PHI",
    "Risk Level",
    "Action",
  ];

  const logRows = () =>
    filtered.map((i) => [
      i.time,
      i.user,
      i.module,
      i.event,
      i.phi,
      i.risk,
      i.action,
    ]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="h-6 w-6" />
            Privacy Incident Logs
          </h2>
          <p className="text-sm text-muted-foreground">
            Comprehensive audit trail of all privacy events and system actions
          </p>
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" />
              Export
            </Button>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={() =>
                downloadCSV("incident-logs", logHeaders, logRows())
              }
            >
              Export as CSV
            </DropdownMenuItem>

            <DropdownMenuItem
              onClick={() =>
                downloadPDF(
                  "incident-logs",
                  "Privacy Incident Logs",
                  logHeaders,
                  logRows(),
                  `${filtered.length} records · Generated on ${new Date().toLocaleString()}`
                )
              }
            >
              Export as PDF
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Card className="glass-card">
        <CardHeader className="pb-2">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="text-base">
              Incident Records ({filtered.length})
            </CardTitle>

            <div className="flex flex-wrap gap-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search..."
                  className="h-8 w-40 pl-8 text-xs bg-muted/50"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>

              <Popover>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className={cn(
                      "h-8 w-56 justify-start text-xs font-normal",
                      !dateRange?.from && "text-muted-foreground"
                    )}
                  >
                    <CalendarIcon className="mr-2 h-3.5 w-3.5" />

                    {dateRange?.from ? (
                      dateRange.to ? (
                        <>
                          {format(dateRange.from, "MMM d")} –{" "}
                          {format(dateRange.to, "MMM d, yyyy")}
                        </>
                      ) : (
                        format(dateRange.from, "MMM d, yyyy")
                      )
                    ) : (
                      "Filter by date range"
                    )}
                  </Button>
                </PopoverTrigger>

                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="range"
                    selected={dateRange}
                    onSelect={setDateRange}
                    numberOfMonths={2}
                    initialFocus
                    className={cn("p-3 pointer-events-auto")}
                  />
                </PopoverContent>
              </Popover>

              {dateRange?.from && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setDateRange(undefined)}
                  title="Clear date filter"
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              )}

              <Select value={riskFilter} onValueChange={setRiskFilter}>
                <SelectTrigger className="h-8 w-28 text-xs">
                  <SelectValue placeholder="Risk" />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="all">All Risks</SelectItem>
                  <SelectItem value="Critical">Critical</SelectItem>
                  <SelectItem value="High">High</SelectItem>
                  <SelectItem value="Medium">Medium</SelectItem>
                  <SelectItem value="Low">Low</SelectItem>
                </SelectContent>
              </Select>

              <Select value={moduleFilter} onValueChange={setModuleFilter}>
                <SelectTrigger className="h-8 w-28 text-xs">
                  <SelectValue placeholder="Module" />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="all">All Modules</SelectItem>
                  <SelectItem value="Module 1">Module 1</SelectItem>
                  <SelectItem value="Module 2">Module 2</SelectItem>
                  <SelectItem value="Module 3">Module 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="overflow-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="py-2 text-left font-medium">Timestamp</th>
                  <th className="py-2 text-left font-medium">User</th>
                  <th className="py-2 text-left font-medium">Module</th>
                  <th className="py-2 text-left font-medium">Event Type</th>
                  <th className="py-2 text-left font-medium">
                    Detected PHI
                  </th>
                  <th className="py-2 text-left font-medium">Risk</th>
                  <th className="py-2 text-left font-medium">Action</th>
                </tr>
              </thead>

              <tbody>
                {filtered.map((i, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-border/50 hover:bg-muted/30"
                  >
                    <td className="py-2.5 font-mono whitespace-nowrap">
                      {i.time}
                    </td>

                    <td className="py-2.5">{i.user}</td>

                    <td className="py-2.5">
                      <Badge variant="outline" className="text-[10px]">
                        {i.module}
                      </Badge>
                    </td>

                    <td className="py-2.5">{i.event}</td>

                    <td className="py-2.5 text-muted-foreground">
                      {i.phi}
                    </td>

                    <td className="py-2.5">
                      <Badge
                        variant="outline"
                        className={riskClass(i.risk)}
                      >
                        {i.risk}
                      </Badge>
                    </td>

                    <td className="py-2.5 text-muted-foreground">
                      {i.action}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}