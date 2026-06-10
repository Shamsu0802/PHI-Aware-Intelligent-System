/*Dashboard.tsx*/ 
import { useState, useEffect } from "react";
import { useCountUp } from "@/hooks/use-count-up";
import {
  MessageSquare,
  ShieldAlert,
  Ban,
  Paperclip,
  Eye,
  Gauge,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Area,
  AreaChart,
  Legend,
} from "recharts";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { useNavigate } from "react-router-dom";
import { downloadCSV, downloadPDF } from "@/lib/export-utils";
import { Download } from "lucide-react";

const metrics = [
  { title: "Messages Scanned Today", value: "1,248", icon: MessageSquare, trend: "+12%", up: true, sparkData: [30, 40, 35, 50, 49, 60, 70, 65, 80], link: "/module-1" },
  { title: "PHI Entities Detected", value: "342", icon: ShieldAlert, trend: "+8%", up: true, sparkData: [20, 25, 22, 30, 28, 35, 40, 38, 42], link: "/module-1" },
  { title: "Blocked Communications", value: "57", icon: Ban, trend: "-3%", up: false, sparkData: [15, 12, 18, 10, 14, 8, 12, 9, 7], link: "/module-2" },
  { title: "Attachments Analyzed", value: "189", icon: Paperclip, trend: "+5%", up: true, sparkData: [10, 15, 12, 18, 20, 22, 19, 25, 28], link: "/module-2" },
  { title: "Unauthorized Screen Views", value: "12", icon: Eye, trend: "-15%", up: false, sparkData: [8, 6, 9, 5, 7, 4, 6, 3, 2], link: "/module-3" },
  { title: "Overall Risk Score", value: "0.34", icon: Gauge, trend: "-7%", up: false, sparkData: [50, 45, 48, 42, 40, 38, 36, 35, 34], link: "/incidents" },
];

const phiDistribution = [
  { name: "Patient Names", count: 128 },
  { name: "Phone Numbers", count: 76 },
  { name: "MRN", count: 52 },
  { name: "Email Addresses", count: 48 },
  { name: "Dates of Birth", count: 38 },
];

const riskData = [
  { name: "Low Risk", value: 45 },
  { name: "Medium Risk", value: 28 },
  { name: "High Risk", value: 18 },
  { name: "Critical Risk", value: 9 },
];

const RISK_COLORS = [
  "hsl(147, 52%, 67%)",
  "hsl(42, 100%, 67%)",
  "hsl(16, 100%, 75%)",
  "hsl(0, 72%, 55%)",
];

const BAR_COLORS = [
  "hsl(213, 58%, 65%)",
  "hsl(168, 45%, 68%)",
  "hsl(16, 100%, 75%)",
  "hsl(147, 52%, 67%)",
  "hsl(42, 100%, 67%)",
];

const alerts = [
  { time: "10:22 AM", phi: "Patient Name", channel: "SMS", risk: "High", action: "Message Masked" },
  { time: "11:05 AM", phi: "MRN", channel: "Email", risk: "Critical", action: "Transmission Blocked" },
  { time: "11:32 AM", phi: "Phone Number", channel: "WhatsApp", risk: "Medium", action: "Alert Raised" },
  { time: "12:15 PM", phi: "Diagnosis", channel: "Fax", risk: "High", action: "Content Redacted" },
  { time: "01:48 PM", phi: "Date of Birth", channel: "Email", risk: "Low", action: "Logged" },
  { time: "02:30 PM", phi: "Email Address", channel: "SMS", risk: "Medium", action: "Alert Raised" },
];

const riskBadgeClass = (risk: string) => {
  switch (risk) {
    case "Critical": return "bg-critical/15 text-critical border-critical/30";
    case "High": return "bg-accent/15 text-accent border-accent/30";
    case "Medium": return "bg-warning/15 text-warning border-warning/30";
    default: return "bg-success/15 text-success border-success/30";
  }
};

const timelineData = [
  { hour: "06:00", scanned: 45, detected: 12 },
  { hour: "08:00", scanned: 120, detected: 35 },
  { hour: "10:00", scanned: 210, detected: 68 },
  { hour: "12:00", scanned: 180, detected: 52 },
  { hour: "14:00", scanned: 250, detected: 78 },
  { hour: "16:00", scanned: 195, detected: 55 },
  { hour: "18:00", scanned: 140, detected: 32 },
  { hour: "20:00", scanned: 108, detected: 10 },
];

const weeklyTrend = [
  { day: "Mon", thisWeek: 312, lastWeek: 280 },
  { day: "Tue", thisWeek: 342, lastWeek: 295 },
  { day: "Wed", thisWeek: 298, lastWeek: 310 },
  { day: "Thu", thisWeek: 378, lastWeek: 325 },
  { day: "Fri", thisWeek: 356, lastWeek: 340 },
  { day: "Sat", thisWeek: 145, lastWeek: 120 },
  { day: "Sun", thisWeek: 98, lastWeek: 85 },
];

const monthlyTrend = [
  { month: "Sep", detections: 4820, blocked: 620, risk: 0.38 },
  { month: "Oct", detections: 5340, blocked: 710, risk: 0.41 },
  { month: "Nov", detections: 5120, blocked: 680, risk: 0.36 },
  { month: "Dec", detections: 6100, blocked: 890, risk: 0.44 },
  { month: "Jan", detections: 5680, blocked: 760, risk: 0.39 },
  { month: "Feb", detections: 6450, blocked: 920, risk: 0.42 },
  { month: "Mar", detections: 4200, blocked: 570, risk: 0.34 },
];

function AnimatedValue({ value }: { value: string }) {
  const display = useCountUp(value);
  return <p className="text-2xl font-bold font-mono">{display}</p>;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [trendView, setTrendView] = useState<"weekly" | "monthly">("weekly");
  const [summary, setSummary] = useState<any>(null);
const [riskDataState, setRiskDataState] = useState<any[]>([]);
const [recentState, setRecentState] = useState<any[]>([]);

useEffect(() => {
  const loadDashboard = async () => {
    try {
      const summaryRes = await fetch("http://127.0.0.1:8000/dashboard/summary");
      const summaryJson = await summaryRes.json();
      setSummary(summaryJson);

      const riskRes = await fetch("http://127.0.0.1:8000/dashboard/risk-distribution");
      const riskJson = await riskRes.json();

      setRiskDataState([
        { name: "Low Risk", value: riskJson.Low || 0 },
        { name: "Medium Risk", value: riskJson.Medium || 0 },
        { name: "High Risk", value: riskJson.High || 0 },
        { name: "Critical Risk", value: riskJson.Critical || 0 },
      ]);

      const recentRes = await fetch("http://127.0.0.1:8000/dashboard/recent-activity");
      const recentJson = await recentRes.json();
      setRecentState(recentJson);

    } catch (err) {
      console.error("Dashboard fetch failed:", err);
    }
  };

  loadDashboard();

  const interval = setInterval(loadDashboard, 3000);

  return () => clearInterval(interval);
}, []);
  const exportMetrics = () => {
    const headers = ["Metric", "Value", "Trend"];
    const rows = metrics.map((m) => [m.title, m.value, m.trend]);
    return { headers, rows };
  };

  const exportAlerts = () => {
    const headers = ["Time", "Detected PHI", "Channel", "Risk Level", "Action"];
    const rows = alerts.map((a) => [a.time, a.phi, a.channel, a.risk, a.action]);
    return { headers, rows };
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">System Dashboard</h2>
          <p className="text-sm text-muted-foreground">Real-time healthcare privacy monitoring overview</p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="h-4 w-4" /> Export
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => { const d = exportMetrics(); downloadCSV("dashboard-metrics", d.headers, d.rows); }}>
              Metrics as CSV
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => { const d = exportMetrics(); downloadPDF("dashboard-metrics", "Dashboard Metrics", d.headers, d.rows, "Generated on " + new Date().toLocaleString()); }}>
              Metrics as PDF
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => { const d = exportAlerts(); downloadCSV("privacy-alerts", d.headers, d.rows); }}>
              Alerts as CSV
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => { const d = exportAlerts(); downloadPDF("privacy-alerts", "Recent Privacy Alerts", d.headers, d.rows, "Generated on " + new Date().toLocaleString()); }}>
              Alerts as PDF
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {[
  {
    ...metrics[0],
    value: summary ? String(summary.total_messages) : "0"
  },
  {
    ...metrics[1],
    value: recentState.reduce((acc, r) => acc + (r.phi_entities || 0), 0).toString()
  },
  {
    ...metrics[2],
    value: summary
      ? String((summary.high_risk || 0) + (summary.medium_risk || 0))
      : "0"
  },
  ...metrics.slice(3)
].map((m) => (
  <Card
    key={m.title} className="glass-card metric-glow cursor-pointer transition-all hover:scale-[1.03] hover:shadow-md" onClick={() => navigate(m.link)}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                  <m.icon className="h-4 w-4 text-primary" />
                </div>
                <div className={`flex items-center gap-1 text-xs font-medium ${m.up ? "text-success" : "text-critical"}`}>
                  {m.up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {m.trend}
                </div>
              </div>
              <AnimatedValue value={m.value} />
              <p className="text-[11px] text-muted-foreground mt-1 leading-tight">{m.title}</p>
              <div className="mt-2 h-8">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={m.sparkData.map((v, i) => ({ i, v }))}>
                    <defs>
                      <linearGradient id={`spark-${m.title}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                        <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <Area type="monotone" dataKey="v" stroke="hsl(var(--primary))" strokeWidth={1.5} fill={`url(#spark-${m.title})`} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Bar Chart */}
        <Card className="glass-card lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">PHI Entity Detection Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={phiDistribution} barSize={32}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: 12,
                    }}
                  />
                  <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                    {phiDistribution.map((_, i) => (
                      <Cell key={i} fill={BAR_COLORS[i % BAR_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Pie Chart */}
        <Card className="glass-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Communication Risk Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDataState.length ? riskDataState : riskData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                  {(riskDataState.length ? riskDataState : riskData).map((_, i) => (
                      <Cell key={i} fill={RISK_COLORS[i]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2">
              {(riskDataState.length ? riskDataState : riskData).map((r, i) => (
                <div key={r.name} className="flex items-center gap-2 text-xs">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: RISK_COLORS[i] }} />
                  <span className="text-muted-foreground">{r.name}</span>
                  <span className="ml-auto font-medium">{r.value}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Timeline + Alerts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Timeline */}
        <Card className="glass-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Scanning Activity Timeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={timelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="hour" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: 12,
                    }}
                  />
                  <Line type="monotone" dataKey="scanned" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="detected" stroke="hsl(var(--accent))" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Alerts Table */}
        <Card className="glass-card">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Recent Privacy Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b text-muted-foreground">
                    <th className="py-2 text-left font-medium">Time</th>
                    <th className="py-2 text-left font-medium">Detected PHI</th>
                    <th className="py-2 text-left font-medium">Channel</th>
                    <th className="py-2 text-left font-medium">Risk</th>
                    <th className="py-2 text-left font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(recentState.length
  ? recentState.map((r: any) => ({
      time: r.timestamp,
      phi: `${r.phi_entities} entities`,
      channel: r.recipient,
      risk: r.risk_level,
      action:
        r.risk_level === "High" || r.risk_level === "Critical"
          ? "Transmission Blocked"
          : "Logged"
    }))
  : alerts
).map((a, i) => (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-2.5 font-mono">{a.time}</td>
                      <td className="py-2.5">{a.phi}</td>
                      <td className="py-2.5">{a.channel}</td>
                      <td className="py-2.5">
                        <Badge variant="outline" className={riskBadgeClass(a.risk)}>{a.risk}</Badge>
                      </td>
                      <td className="py-2.5 text-muted-foreground">{a.action}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Trend Comparison */}
      <Card className="glass-card">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">PHI Detection Trends</CardTitle>
            <div className="flex rounded-lg bg-muted p-0.5">
              <button
                onClick={() => setTrendView("weekly")}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${trendView === "weekly" ? "bg-card shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              >
                Weekly
              </button>
              <button
                onClick={() => setTrendView("monthly")}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${trendView === "monthly" ? "bg-card shadow-sm text-foreground" : "text-muted-foreground hover:text-foreground"}`}
              >
                Monthly
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              {trendView === "weekly" ? (
                <BarChart data={weeklyTrend} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="thisWeek" name="This Week" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} barSize={20} />
                  <Bar dataKey="lastWeek" name="Last Week" fill="hsl(var(--primary) / 0.3)" radius={[4, 4, 0, 0]} barSize={20} />
                </BarChart>
              ) : (
                <LineChart data={monthlyTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis yAxisId="left" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" domain={[0, 1]} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: "8px", fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line yAxisId="left" type="monotone" dataKey="detections" name="Detections" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 3 }} />
                  <Line yAxisId="left" type="monotone" dataKey="blocked" name="Blocked" stroke="hsl(var(--chart-3))" strokeWidth={2} dot={{ r: 3 }} />
                  <Line yAxisId="right" type="monotone" dataKey="risk" name="Risk Score" stroke="hsl(var(--chart-5))" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 3 }} />
                </LineChart>
              )}
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
