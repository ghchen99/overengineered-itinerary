'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { BotIcon, CheckCircleIcon, ClockIcon } from 'lucide-react';
import { AgentActivity } from '@/types';

interface AgentActivityProps {
  agents: AgentActivity[];
  totalMessages: number;
}

export function AgentActivityDisplay({ agents, totalMessages }: AgentActivityProps) {
  if (agents.length === 0) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BotIcon className="h-5 w-5" />
          Agent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Total Messages: {totalMessages}</span>
            <span>Active Agents: {agents.filter(a => a.status === 'active').length}</span>
          </div>
          
          <div className="space-y-3">
            {agents.map((agent) => (
              <div key={agent.agent} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <BotIcon className="h-4 w-4" />
                    {agent.status === 'active' && (
                      <div className="absolute -top-1 -right-1 h-2 w-2 bg-green-500 rounded-full animate-pulse" />
                    )}
                  </div>
                  <div>
                    <div className="font-medium">{agent.agent}</div>
                    <div className="text-xs text-muted-foreground">
                      {agent.lastActivity}
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Badge variant={
                    agent.status === 'active' ? 'default' :
                    agent.status === 'completed' ? 'secondary' : 'outline'
                  }>
                    {agent.status === 'active' && <ClockIcon className="h-3 w-3 mr-1" />}
                    {agent.status === 'completed' && <CheckCircleIcon className="h-3 w-3 mr-1" />}
                    {agent.status}
                  </Badge>
                  <Badge variant="outline">
                    {agent.taskCount} tasks
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}