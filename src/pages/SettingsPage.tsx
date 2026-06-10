import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Settings as SettingsIcon, Save } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

export default function SettingsPage() {
  const [sensitivity, setSensitivity] = useState([75]);
  const [riskThreshold, setRiskThreshold] = useState([60]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold flex items-center gap-2"><SettingsIcon className="h-6 w-6" /> System Settings</h2>
        <p className="text-sm text-muted-foreground">Configure system parameters and detection thresholds</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="glass-card">
          <CardHeader className="pb-2"><CardTitle className="text-base">Detection Configuration</CardTitle></CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm">PHI Detection Sensitivity</Label>
                <span className="text-sm font-mono font-bold text-primary">{sensitivity[0]}%</span>
              </div>
              <Slider value={sensitivity} onValueChange={setSensitivity} max={100} step={5} />
              <p className="text-[11px] text-muted-foreground">Higher values detect more PHI but may increase false positives</p>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm">Risk Threshold</Label>
                <span className="text-sm font-mono font-bold text-warning">{riskThreshold[0]}%</span>
              </div>
              <Slider value={riskThreshold} onValueChange={setRiskThreshold} max={100} step={5} />
              <p className="text-[11px] text-muted-foreground">Communications above this threshold will be blocked</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm">Default Blocking Action</Label>
              <Select defaultValue="mask">
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="mask">Mask PHI Entities</SelectItem>
                  <SelectItem value="block">Block Transmission</SelectItem>
                  <SelectItem value="alert">Alert Only</SelectItem>
                  <SelectItem value="log">Log & Allow</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="pb-2"><CardTitle className="text-base">Communication Channels</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {["Email (SMTP/TLS)", "SMS", "WhatsApp", "Fax", "Hospital Portal"].map((ch) => (
              <div key={ch} className="flex items-center justify-between">
                <Label className="text-sm">{ch}</Label>
                <Switch defaultChecked={ch !== "Fax"} />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="pb-2"><CardTitle className="text-base">Alert Preferences</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {["Email Notifications", "Dashboard Alerts", "SMS Alerts", "Auto Screen Blur"].map((pref) => (
              <div key={pref} className="flex items-center justify-between">
                <Label className="text-sm">{pref}</Label>
                <Switch defaultChecked />
              </div>
            ))}
            <div className="space-y-2">
              <Label className="text-sm">Admin Email</Label>
              <Input placeholder="admin@hospital.com" className="bg-muted/50" />
            </div>
          </CardContent>
        </Card>

        <Card className="glass-card">
          <CardHeader className="pb-2"><CardTitle className="text-base">Authorized Face Database</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {["Dr. Meena Sharma", "Nurse Priya Nair", "Dr. Anand Kumar", "Admin Ravi Verma"].map((name) => (
              <div key={name} className="flex items-center justify-between rounded-lg bg-muted/50 p-2.5">
                <span className="text-sm">{name}</span>
                <span className="text-xs text-success font-medium">Enrolled</span>
              </div>
            ))}
            <Button variant="outline" size="sm" className="w-full">+ Add Authorized Face</Button>
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end">
        <Button onClick={() => toast.success("Settings saved successfully")} className="gap-2">
          <Save className="h-4 w-4" /> Save Settings
        </Button>
      </div>
    </div>
  );
}
