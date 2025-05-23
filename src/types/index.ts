export interface Lead {
  id: string;
  email: string;
  name?: string;
  company?: string;
  status: 'new' | 'emailed' | 'responded' | 'bounced' | 'blacklisted';
  lastContacted: Date | null;
  followupCount: number;
  createdAt: Date;
  projectId: string;
  interactionSummary: string; // Summary of past interactions
  emailChain: EmailRecord[]; // Full email chain
  source?: string; // How the lead was acquired
  notes?: string;
}

export interface EmailRecord {
  id: string;
  type: 'outreach' | 'followup' | 'response';
  subject: string;
  content: string;
  sentAt: Date;
  projectId: string;
  leadId: string;
}

export interface Project {
  id: string;
  name: string;
  areaDescription: string; // Exact address and specification
  projectDetails: string; // Max 5k characters
  emailConsiderations: string; // Max 300 characters
  followupConsiderations: string; // Max 300 characters
  createdAt: Date;
  updatedAt: Date;
  isActive: boolean;
  leadCount: number;
}

export interface GlobalSettings {
  followupDelayDays: number;
  maxFollowups: number;
}

export interface ApiKeys {
  openaiApiKey: string;
  apolloApiKey: string;
  apifiApiKey: string;
  perplexityApiKey: string;
}

export interface Prompts {
  outreachPrompt: string;
  followupPrompt: string;
}

// Global prompts (default templates)
export type GlobalPrompts = Prompts;

// Project-specific prompts (can override global)
export interface ProjectPrompts extends Prompts {
  projectId: string;
  useGlobalPrompts: boolean;
}

export interface BlacklistEmails {
  list: string[];
  projectId?: string; // If null, it's global blacklist
}

export interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
}

export interface LeadImport {
  email: string;
  name?: string;
  company?: string;
  source?: string;
  notes?: string;
} 