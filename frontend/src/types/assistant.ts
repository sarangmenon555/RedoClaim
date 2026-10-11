export interface AssistantField {
  key: string;
  label: string;
  kind: "document" | "value";
  hint?: string;
}

export interface AssistantModule {
  id: string;
  label: string;
  status: "ok" | "unavailable" | "error";
  highlights: string[];
  data: Record<string, any>;
  links: { label: string; href: string }[];
  message?: string | null;
}

export interface AssistantNeed {
  intent: string;
  label: string;
  question: string | null;
  fields: AssistantField[];
}

export interface AssistantContext {
  params: Record<string, any>;
  claim_id: string | null;
  pending: { intent: string; missing: string[] }[];
}

export interface AssistantDocument {
  id: string;
  file_name: string;
  kind: string;
  label: string;
}

export interface AssistantReply {
  answer: string;
  language: string;
  modules: AssistantModule[];
  needs: AssistantNeed[];
  suggestions: { id: string; label: string; message: string }[];
  documents: AssistantDocument[];
  context: AssistantContext;
  ai_disclaimer: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  files?: { name: string; label?: string }[];
  reply?: AssistantReply;
  error?: boolean;
}
