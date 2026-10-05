import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, AlertTriangle, Users } from "lucide-react"
import { RealTimeCharts } from "./real-time-charts"
import { LiveMetrics } from "./live-metrics"

export function DashboardContent() {
  return (
    <div className="space-y-6">
      {/* Live Metrics */}
      <LiveMetrics />

      {/* Real-time Charts */}
      <RealTimeCharts />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* City Overview Map Placeholder */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>City Overview</CardTitle>
            <CardDescription>Real-time monitoring of urban systems</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-96 bg-muted/20 rounded-lg border-2 border-dashed border-urban-grid flex items-center justify-center">
              <div className="text-center">
                <div className="text-lg font-medium text-muted-foreground mb-2">Interactive City Map</div>
                <div className="text-sm text-muted-foreground">Real-time data visualization will be displayed here</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
            <CardDescription>Latest system notifications</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                <AlertTriangle className="h-4 w-4 text-destructive mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm font-medium">Traffic Incident</div>
                  <div className="text-xs text-muted-foreground">Main St & 5th Ave - 2 min ago</div>
                </div>
                <Badge variant="destructive" className="text-xs">
                  High
                </Badge>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg bg-urban-warning/10 border border-urban-warning/20">
                <Activity className="h-4 w-4 text-urban-warning mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm font-medium">Air Quality Alert</div>
                  <div className="text-xs text-muted-foreground">Downtown area - 15 min ago</div>
                </div>
                <Badge variant="outline" className="text-xs border-urban-warning text-urban-warning">
                  Medium
                </Badge>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg bg-urban-info/10 border border-urban-info/20">
                <Users className="h-4 w-4 text-urban-info mt-0.5" />
                <div className="flex-1">
                  <div className="text-sm font-medium">Crowd Density</div>
                  <div className="text-xs text-muted-foreground">Central Park - 1 hour ago</div>
                </div>
                <Badge variant="outline" className="text-xs border-urban-info text-urban-info">
                  Info
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
