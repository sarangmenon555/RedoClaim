import { create } from "zustand";
import type { AssistantContext, ChatMessage } from "@/types/assistant";

const emptyContext: AssistantContext = { params: {}, claim_id: null, pending: [] };

interface AssistantState {
  messages: ChatMessage[];
  documentIds: string[];
  context: AssistantContext;
  busy: boolean;
  addMessage: (message: ChatMessage) => void;
  addDocuments: (ids: string[]) => void;
  setContext: (context: AssistantContext) => void;
  setBusy: (busy: boolean) => void;
  reset: () => void;
}

export const useAssistantStore = create<AssistantState>()((set) => ({
  messages: [],
  documentIds: [],
  context: emptyContext,
  busy: false,
  addMessage: (message) => set((s) => ({ messages: [...s.messages, message] })),
  addDocuments: (ids) => set((s) => ({ documentIds: Array.from(new Set([...s.documentIds, ...ids])) })),
  setContext: (context) => set({ context }),
  setBusy: (busy) => set({ busy }),
  reset: () => set({ messages: [], documentIds: [], context: emptyContext, busy: false }),
}));
