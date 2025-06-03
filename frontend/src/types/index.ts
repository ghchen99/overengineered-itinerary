export interface TravelRequest {
  destination_city: string;
  destination_country: string;
  depart_date: string;
  return_date: string;
  priority: 'food' | 'culture' | 'history' | 'adventure' | 'relaxation';
  budget_level: 'budget' | 'moderate' | 'flexible' | 'luxury';
  departure_airport: string;
  destination_airport?: string;
  additional_preferences?: string;
}

export interface StreamMessage {
  type: 'progress' | 'markdown_update' | 'final' | 'error';
  agent?: string;
  content: string;
  timestamp: string;
  character_count?: number;
}

export interface AgentActivity {
  agent: string;
  lastActivity: string;
  status: 'active' | 'completed' | 'idle';
  taskCount: number;
}