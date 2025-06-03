'use client';

import { useState, useCallback, useEffect } from 'react';
import { TravelPlannerForm } from './TravelPlannerForm';
import { AgentActivityDisplay } from './AgentActivity';
import { MarkdownRenderer } from './MarkdownRenderer';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { AlertCircleIcon, RefreshCwIcon } from 'lucide-react';
import { TravelPlannerAPI } from '@/lib/api';
import { TravelRequest, StreamMessage, AgentActivity } from '@/types';
import { formatDistanceToNow } from 'date-fns';

export function StreamingDisplay() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState<boolean | null>(null);
  
  // Streaming state
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [agents, setAgents] = useState<AgentActivity[]>([]);
  const [currentMarkdown, setCurrentMarkdown] = useState('');
  const [characterCount, setCharacterCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  const api = new TravelPlannerAPI();

  const checkConnection = useCallback(async () => {
    try {
      const healthy = await api.checkHealth();
      setIsConnected(healthy);
      if (!healthy) {
        setError('Cannot connect to Travel Planner API. Make sure the server is running on localhost:8000');
      } else {
        setError(null);
      }
    } catch (err) {
      setIsConnected(false);
      setError('Failed to connect to the API server');
    }
  }, []);

  const updateAgentActivity = useCallback((message: StreamMessage) => {
    if (!message.agent) return;

    const agentName = message.agent; // TypeScript now knows this is string (not undefined)

    setAgents(prev => {
      const existing = prev.find(a => a.agent === agentName);
      const now = new Date().toLocaleTimeString();
      
      if (existing) {
        return prev.map(agent => 
          agent.agent === agentName
            ? {
                ...agent,
                lastActivity: message.content.substring(0, 50) + (message.content.length > 50 ? '...' : ''),
                status: message.type === 'final' ? 'completed' as const : 'active' as const,
                taskCount: agent.taskCount + 1,
              }
            : agent
        );
      } else {
        return [...prev, {
          agent: agentName,
          lastActivity: message.content.substring(0, 50) + (message.content.length > 50 ? '...' : ''),
          status: 'active' as const,
          taskCount: 1,
        }];
      }
    });
  }, []);

  const handleSubmit = useCallback(async (request: TravelRequest) => {
    setIsLoading(true);
    setError(null);
    setMessages([]);
    setAgents([]);
    setCurrentMarkdown('');
    setCharacterCount(0);
    setLastUpdate('');

    try {
      const stream = api.streamTravelPlan(request);
      
      for await (const message of stream) {
        setMessages(prev => [...prev, message]);
        updateAgentActivity(message);
        
        if (message.type === 'markdown_update' || message.type === 'final') {
          setIsUpdating(true);
          setCurrentMarkdown(message.content);
          setCharacterCount(message.character_count || message.content.length);
          setLastUpdate(formatDistanceToNow(new Date(message.timestamp), { addSuffix: true }));
          
          // Remove updating indicator after a short delay
          setTimeout(() => setIsUpdating(false), 1000);
        }
        
        if (message.type === 'final') {
          // Mark all agents as completed
          setAgents(prev => prev.map(agent => ({ ...agent, status: 'completed' as const })));
          break;
        }
        
        if (message.type === 'error') {
          setError(message.content);
          break;
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setIsLoading(false);
    }
  }, [api, updateAgentActivity]);

  // Check connection on mount
  useEffect(() => {
    checkConnection();
  }, [checkConnection]);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 space-y-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Ctrl+Trip</h1>
          <p className="text-muted-foreground">
            No humans were stressed in the making of this trip.
          </p>
        </div>

        {/* Connection Status */}
        {isConnected === false && (
          <Alert>
            <AlertCircleIcon className="h-4 w-4" />
            <AlertDescription className="flex items-center justify-between">
              <span>API Server not connected. Make sure it's running on localhost:8000</span>
              <Button variant="outline" size="sm" onClick={checkConnection}>
                <RefreshCwIcon className="h-4 w-4 mr-2" />
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertCircleIcon className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Main Form - Only show when not loading and no messages */}
        {!isLoading && messages.length === 0 && (
          <TravelPlannerForm onSubmit={handleSubmit} isLoading={isLoading} />
        )}

        {/* Results Section - Show when loading or have messages */}
        {(isLoading || messages.length > 0) && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Agent Activity - Takes 1/3 width on large screens */}
              <div className="lg:col-span-1">
                <AgentActivityDisplay agents={agents} totalMessages={messages.length} />
              </div>
              
              {/* Markdown Content - Takes 2/3 width on large screens */}
              <div className="lg:col-span-2">
                <MarkdownRenderer
                  content={currentMarkdown}
                  characterCount={characterCount}
                  isUpdating={isUpdating}
                  lastUpdate={lastUpdate}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}