"use client"

import { useState, useRef, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  MessageSquare,
  Send,
  Bot,
  User,
  AlertTriangle,
  TrendingUp,
  MapPin,
  Zap,
  Activity,
  Shield,
  Car,
} from "lucide-react"

interface ChatMessage {
  id: string
  type: "user" | "assistant"
  content: string
  timestamp: Date
  context?: {
    type: "alert" | "metric" | "location" | "analysis"
    data?: any
  }
}

interface QuickQuery {
  id: string
  title: string
  query: string
  category: "safety" | "traffic" | "planning" | "general"
  icon: any
}

const quickQueries: QuickQuery[] = [
  {
    id: "1",
    title: "Current Traffic Status",
    query: "What's the current traffic situation in downtown?",
    category: "traffic",
    icon: Car,
  },
  {
    id: "2",
    title: "Active Safety Incidents",
    query: "Show me all active public safety incidents",
    category: "safety",
    icon: Shield,
  },
  {
    id: "3",
    title: "Air Quality Analysis",
    query: "How is the air quality today and what are the trends?",
    category: "planning",
    icon: Activity,
  },
  {
    id: "4",
    title: "Route Optimization",
    query: "What's the fastest route from City Hall to the airport right now?",
    category: "planning",
    icon: MapPin,
  },
  {
    id: "5",
    title: "Emergency Response",
    query: "What's the average emergency response time this week?",
    category: "safety",
    icon: AlertTriangle,
  },
  {
    id: "6",
    title: "Energy Usage",
    query: "Show me the current city energy consumption patterns",
    category: "general",
    icon: Zap,
  },
]





export function AIAssistantDashboard() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      type: "assistant",
      content:
        "Hello! I'm your Urban Intelligence AI Assistant. I can help you analyze city data, monitor public safety, optimize routes, and provide insights about urban planning. What would you like to know?",
      timestamp: new Date(),
    },
  ])
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setIsTyping(true)

    try {
      const response = await fetch("http://localhost:8000/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: content }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const resData = await response.json()
      const aiContent = resData.answer || "No answer returned by backend."

      const aiResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: aiContent,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, aiResponse])
    } catch (err) {
      const errorResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "AI Copilot unavailable — Unable to reach backend server (http://localhost:8000/api/ask). Ensure backend is running via `python -m src.main`.",
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorResponse])
    } finally {
      setIsTyping(false)
    }
  }


  const handleQuickQuery = (query: QuickQuery) => {
    handleSendMessage(query.query)
  }

  const getCategoryColor = (category: QuickQuery["category"]) => {
    switch (category) {
      case "safety":
        return "border-urban-danger text-urban-danger bg-urban-danger/10"
      case "traffic":
        return "border-urban-warning text-urban-warning bg-urban-warning/10"
      case "planning":
        return "border-urban-success text-urban-success bg-urban-success/10"
      default:
        return "border-urban-info text-urban-info bg-urban-info/10"
    }
  }

  return (
    <div className="space-y-6">
      {/* AI Assistant Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-balance">Urban Intelligence AI Assistant</h2>
          <p className="text-muted-foreground">
            Get real-time insights and analysis of city data through natural language queries
          </p>
        </div>
        <Badge className="text-urban-success border-urban-success bg-urban-success/10">
          <div className="w-2 h-2 bg-urban-success rounded-full mr-2 animate-pulse" />
          AI Online
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Chat Interface */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Chat with AI Assistant
            </CardTitle>
            <CardDescription>Ask questions about city operations, safety, traffic, and planning</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Messages */}
            <ScrollArea className="h-96 w-full rounded-lg border p-4">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${message.type === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div className={`flex gap-3 max-w-[80%] ${message.type === "user" ? "flex-row-reverse" : ""}`}>
                      <div className="flex-shrink-0 mt-1">
                        {message.type === "user" ? (
                          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                            <User className="h-4 w-4 text-primary-foreground" />
                          </div>
                        ) : (
                          <div className="w-8 h-8 rounded-full bg-urban-info flex items-center justify-center">
                            <Bot className="h-4 w-4 text-white" />
                          </div>
                        )}
                      </div>
                      <div
                        className={`rounded-lg p-3 ${
                          message.type === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                        }`}
                      >
                        <p className="text-sm leading-relaxed">{message.content}</p>
                        <p className="text-xs opacity-70 mt-1">{message.timestamp.toLocaleTimeString()}</p>
                      </div>
                    </div>
                  </div>
                ))}
                {isTyping && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-urban-info flex items-center justify-center">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                    <div className="bg-muted rounded-lg p-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-100" />
                        <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce delay-200" />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="flex gap-2">
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask about traffic, safety, air quality, or city planning..."
                onKeyPress={(e) => e.key === "Enter" && handleSendMessage(inputValue)}
                className="flex-1"
              />
              <Button onClick={() => handleSendMessage(inputValue)} disabled={!inputValue.trim() || isTyping}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Quick Queries & Context */}
        <div className="space-y-6">
          {/* Quick Queries */}
          <Card>
            <CardHeader>
              <CardTitle>Quick Queries</CardTitle>
              <CardDescription>Common questions and analysis requests</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {quickQueries.map((query) => (
                  <Button
                    key={query.id}
                    variant="outline"
                    className={`w-full justify-start text-left h-auto p-3 ${getCategoryColor(query.category)}`}
                    onClick={() => handleQuickQuery(query)}
                  >
                    <query.icon className="h-4 w-4 mr-2 flex-shrink-0" />
                    <span className="text-sm">{query.title}</span>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* AI Capabilities */}
          <Card>
            <CardHeader>
              <CardTitle>AI Capabilities</CardTitle>
              <CardDescription>What I can help you with</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <Shield className="h-4 w-4 text-urban-danger mt-0.5" />
                  <div>
                    <div className="font-medium">Public Safety</div>
                    <div className="text-muted-foreground text-xs">
                      Monitor incidents, response times, and emergency patterns
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <Car className="h-4 w-4 text-urban-warning mt-0.5" />
                  <div>
                    <div className="font-medium">Traffic Analysis</div>
                    <div className="text-muted-foreground text-xs">
                      Real-time traffic flow, congestion, and route optimization
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <MapPin className="h-4 w-4 text-urban-success mt-0.5" />
                  <div>
                    <div className="font-medium">Urban Planning</div>
                    <div className="text-muted-foreground text-xs">
                      Infrastructure analysis, sustainability metrics, and planning insights
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <TrendingUp className="h-4 w-4 text-urban-info mt-0.5" />
                  <div>
                    <div className="font-medium">Predictive Analytics</div>
                    <div className="text-muted-foreground text-xs">Trend analysis and future scenario modeling</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
