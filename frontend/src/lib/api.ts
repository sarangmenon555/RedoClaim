import axios, { AxiosError } from "axios";
import { getCurrentLanguage } from "@/store/language";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://redoclaim-backend.onrender.com";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 180000,
  headers: { "Content-Type": "application/json" },
  // Required so the browser sends/receives the httpOnly refresh-token
  // cookie (see backend auth.py) on cross-origin requests to the API.
  withCredentials: true,
});

// ── Token helpers ─────────────────────────────────────────────────────────────
// Only the short-lived access token lives in JS-reachable storage now. The
// refresh token is an httpOnly cookie the backend sets on login/register/
// refresh — it is never exposed to JavaScript, so an XSS bug can no longer
// steal it and mint itself new sessions indefinitely the way it could
// before. An XSS can still steal the access token in memory/localStorage
// for its (short) lifetime, but that's a much smaller blast radius.

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setAccessToken(access_token: string): void {
  localStorage.setItem("access_token", access_token);
}

export function clearTokens(): void {
  localStorage.removeItem("access_token");
  // Old key, in case a still-logged-in browser has it from before this change.
  localStorage.removeItem("refresh_token");
}

// ── Request interceptor — attach Bearer token ─────────────────────────────────

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  // Tell the backend which regional language to reply in — read by the
  // get_request_language dependency (X-Language header). Individual
  // request bodies can still pass their own output_language to override.
  config.headers["X-Language"] = getCurrentLanguage();
  return config;
});

// ── Response interceptor — silent token refresh on 401 ───────────────────────

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const isUnauthorized = error.response?.status === 401;
    const isRefreshEndpoint = error.config?.url?.includes("/auth/refresh");

    if (isUnauthorized && !isRefreshEndpoint && typeof window !== "undefined") {
      try {
        // No token passed in the body anymore — the refresh token rides
        // along automatically as the httpOnly cookie (withCredentials above).
        const res = await axios.post(
          `${API_URL}/api/v1/auth/refresh`,
          {},
          { withCredentials: true }
        );
        const { access_token } = res.data;
        setAccessToken(access_token);

        if (error.config) {
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return api.request(error.config);
        }
      } catch {
        clearTokens();
        window.location.href = "/auth/login";
      }
    }

    return Promise.reject(error);
  }
);

// ── Auth API ──────────────────────────────────────────────────────────────────

export const authApi = {
  register: async (data: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
  }) => {
    const res = await api.post("/auth/register", data);
    setAccessToken(res.data.access_token);
    return res;
  },

  login: async (email: string, password: string) => {
    const form = new FormData();
    form.append("username", email);
    form.append("password", password);
    const res = await api.post("/auth/login", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    setAccessToken(res.data.access_token);
    return res;
  },

  me: () => api.get("/auth/me"),

  // Update profile — name and/or phone and/or preferred report language
  updateProfile: (data: { full_name?: string; phone?: string | null; preferred_language?: string }) =>
    api.patch("/auth/me", data),

  // Change password
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/auth/me/password", data),

  // Delete account — permanently removes all user data
  deleteAccount: () => api.delete("/auth/me"),

  // Request a password-reset email/link (see backend /auth/forgot-password).
  forgotPassword: (email: string) => api.post("/auth/forgot-password", { email }),

  // Complete a password reset with the token from the reset link.
  resetPassword: (token: string, newPassword: string) =>
    api.post("/auth/reset-password", { token, new_password: newPassword }),

  logout: () => {
    // Best-effort: clears the httpOnly refresh cookie server-side. Client
    // state is cleared either way even if this call fails (e.g. offline).
    api.post("/auth/logout").catch(() => {});
    clearTokens();
    window.location.href = "/auth/login";
  },
};

// ── Documents API ─────────────────────────────────────────────────────────────

export const documentsApi = {
  upload: (file: File, docType: string, insuranceType?: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("doc_type", docType);
    if (insuranceType) form.append("insurance_type", insuranceType);
    return api.post("/documents/upload", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 300000,
    });
  },
  list: () => api.get("/documents/"),
  get: (id: string) => api.get(`/documents/${id}`),
  getPolicySummary: (id: string) => api.get(`/analysis/policy/${id}/summary`),
};

// ── Analysis API ──────────────────────────────────────────────────────────────

export const analysisApi = {
  auditRejection: (data: {
    rejection_document_id: string;
    policy_document_id?: string;
    cis_document_id?: string;
    insurer_name: string;
    policy_number: string;
    claim_amount?: number;
    insurance_type: string;
    claim_date?: string;
    rejection_date?: string;
    gro_filed?: boolean;
    gro_filed_date?: string;
    survey_appointment_date?: string;
    survey_report_date?: string;
    policy_inception_date?: string;
    documents_complete_date?: string;
    // Family/dependent linking — who this claim is for, if not the
    // account holder (spouse/parent/child under a family floater policy).
    patient_name?: string;
    patient_relationship?: string;
    // Regional language output: en, hi, ml, ta, te, kn. Defaults to English
    // when omitted — pass the active UI language to get the audit report
    // back in Malayalam/Tamil/Telugu/Kannada/Hindi.
    output_language?: string;
  }) => api.post("/analysis/audit-rejection", data),

  scanCIS: (documentId: string) => api.post(`/analysis/scan-cis/${documentId}`),

  portabilityGuide: (data: {
    policy_document_id: string;
    years_covered: number;
    reason_for_porting: string;
  }) => api.post("/analysis/portability-guide", data),

  edaakhilGuide: () => api.get("/analysis/edaakhil-guide"),

  // Free-form question answered by the backend's function-calling agent
  // (GPT-5 Nano + tools: claim lookup, policy clauses, IRDAI search,
  // deadline calc, redressal routing, appeal-draft saving). See
  // POST /analysis/ask on the backend.
  ask: (question: string, claimId?: string) =>
    api.post("/analysis/ask", { question, claim_id: claimId }),

  // Deterministic (no LLM) itemized payout estimate computed from a
  // document's already-extracted policy clauses. See
  // POST /analysis/estimate-payout on the backend.
  estimatePayout: (documentId: string, claimAmount: number, claimId?: string, patientAge?: number) =>
    api.post("/analysis/estimate-payout", {
      document_id: documentId,
      claim_amount: claimAmount,
      claim_id: claimId,
      patient_age: patientAge,
    }),

  // Deterministic (no LLM) waiting-period lapse check computed from a
  // policy's already-extracted waiting_periods clauses + inception date.
  checkWaitingPeriods: (documentId: string, asOfDate?: string) =>
    api.post("/analysis/waiting-period-check", { document_id: documentId, as_of_date: asOfDate }),

  // Side-by-side comparison of 2-3 already-analyzed policies. No new LLM call.
  comparePolicies: (documentIds: string[]) =>
    api.post("/analysis/compare-policies", { document_ids: documentIds }),

  // Plain-language explanation of any insurance term or clause.
  explainTerm: (termOrClause: string, outputLanguage: string = "en") =>
    api.post("/analysis/explain-term", { term_or_clause: termOrClause, output_language: outputLanguage }),
};

// ── Appeals API ───────────────────────────────────────────────────────────────

export const appealsApi = {
  generate: (claimId: string, appealType: string, additionalContext?: string) =>
    api.post("/appeals/generate", {
      claim_id: claimId,
      appeal_type: appealType,
      additional_context: additionalContext,
    }),
  listForClaim: (claimId: string) => api.get(`/appeals/claim/${claimId}`),
  get: (id: string) => api.get(`/appeals/${id}`),
  updateOutcome: (id: string, outcome: "pending" | "approved" | "rejected" | "partial", submittedAt?: string) =>
    api.patch(`/appeals/${id}/outcome`, { outcome, submitted_at: submittedAt }),
};

// ── Claims API ────────────────────────────────────────────────────────────────

export const claimsApi = {
  list: (patientName?: string) =>
    api.get("/claims/", { params: patientName !== undefined ? { patient_name: patientName } : {} }),
  get: (id: string) => api.get(`/claims/${id}`),
  getTimeline: (id: string) => api.get(`/claims/${id}/timeline`),
  updatePatient: (id: string, data: { patient_name: string | null; patient_relationship: string | null }) =>
    api.put(`/claims/${id}/patient`, data),
  listPatients: () => api.get("/claims/patients"),
  getUrgentDeadlines: () => api.get("/claims/deadlines/urgent"),
  exportPdf: (id: string) => api.get(`/claims/${id}/export-pdf`, { responseType: "blob" }),
};

// ── Language API — regional language support (Sarvam AI) ───────────────────────

export const languageApi = {
  // List of languages RedoClaim supports for translated output.
  getSupported: () => api.get("/language/supported"),

  // Translate arbitrary text (e.g. a document summary, a custom note).
  translate: (text: string, targetLanguage: string, sourceLanguage = "auto") =>
    api.post("/language/translate", {
      text,
      target_language: targetLanguage,
      source_language: sourceLanguage,
    }),

  // Convert script (e.g. romanized text -> Malayalam script).
  transliterate: (text: string, targetLanguage: string, sourceLanguage = "auto") =>
    api.post("/language/transliterate", {
      text,
      target_language: targetLanguage,
      source_language: sourceLanguage,
    }),

  detect: (text: string) => api.post("/language/detect", { text }),

  // Fetch a saved claim's audit report translated into targetLanguage.
  // Cached server-side after the first call for that language.
  translateClaimReport: (claimId: string, targetLanguage: string) =>
    api.get(`/language/claims/${claimId}/translate`, {
      params: { target_language: targetLanguage },
    }),
};