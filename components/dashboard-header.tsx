import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Bell, Settings, User, Activity } from "lucide-react"

export function DashboardHeader() {
  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left side - Title and status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Activity className="h-6 w-6 text-primary" />
            <h1 className="text-xl font-semibold text-balance">Urban Intelligence Copilot</h1>
          </div>
          <Badge variant="outline" className="text-urban-success border-urban-success">
            <div className="w-2 h-2 bg-urban-success rounded-full mr-2 animate-pulse" />
            Live
          </Badge>
        </div>

        {/* Right side - Controls */}
        <div className="flex items-center gap-3">
          <div className="text-sm text-muted-foreground">Last updated: {new Date().toLocaleTimeString()}</div>
          <Button variant="ghost" size="sm">
            <Bell className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <Settings className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="sm">
            <User className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}
