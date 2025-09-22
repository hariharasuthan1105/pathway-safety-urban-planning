"use client"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { LayoutDashboard, Shield, MapPin, MessageSquare, AlertTriangle, Users, Car, Zap, Wind } from "lucide-react"

const navigationItems = [
  {
    title: "Overview",
    icon: LayoutDashboard,
    key: "overview",
    badge: null,
  },
  {
    title: "Public Safety",
    icon: Shield,
    key: "safety",
    badge: { text: "3", variant: "destructive" as const },
  },
  {
    title: "Urban Planning",
    icon: MapPin,
    key: "planning",
    badge: null,
  },
  {
    title: "AI Assistant",
    icon: MessageSquare,
    key: "assistant",
    badge: null,
  },
]

const dataCategories = [
  {
    title: "Traffic Flow",
    icon: Car,
    status: "normal",
    value: "2.3K",
  },
  {
    title: "Air Quality",
    icon: Wind,
    status: "warning",
    value: "Moderate",
  },
  {
    title: "Emergency",
    icon: AlertTriangle,
    status: "alert",
    value: "3 Active",
  },
  {
    title: "Population",
    icon: Users,
    status: "normal",
    value: "847K",
  },
  {
    title: "Power Grid",
    icon: Zap,
    status: "normal",
    value: "98.2%",
  },
]

interface DashboardSidebarProps {
  activeView?: string
  onViewChange?: (view: string) => void
}

export function DashboardSidebar({ activeView = "overview", onViewChange }: DashboardSidebarProps) {
  return (
    <aside className="w-64 bg-sidebar border-r border-sidebar-border">
      <div className="flex flex-col h-full">
        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-2">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Navigation</h2>
            {navigationItems.map((item) => (
              <Button
                key={item.title}
                variant={activeView === item.key ? "secondary" : "ghost"}
                className={cn(
                  "w-full justify-start gap-3 h-10",
                  activeView === item.key && "bg-sidebar-accent text-sidebar-accent-foreground",
                )}
                onClick={() => onViewChange?.(item.key)}
              >
                <item.icon className="h-4 w-4" />
                <span className="flex-1 text-left">{item.title}</span>
                {item.badge && (
                  <Badge variant={item.badge.variant} className="text-xs">
                    {item.badge.text}
                  </Badge>
                )}
              </Button>
            ))}
          </div>

          {/* Data Sources */}
          <div className="mt-8">
            <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-4">Live Data</h2>
            <div className="space-y-3">
              {dataCategories.map((category) => (
                <div
                  key={category.title}
                  className="flex items-center justify-between p-2 rounded-lg bg-sidebar-accent/50"
                >
                  <div className="flex items-center gap-2">
                    <category.icon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{category.title}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{category.value}</span>
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full",
                        category.status === "normal" && "bg-urban-success",
                        category.status === "warning" && "bg-urban-warning",
                        category.status === "alert" && "bg-urban-danger animate-pulse",
                      )}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-sidebar-border">
          <div className="text-xs text-muted-foreground">
            <div>System Status: Operational</div>
            <div>Data Sources: 12 Active</div>
          </div>
        </div>
      </div>
    </aside>
  )
}
