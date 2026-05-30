import axios, { AxiosError } from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://redoclaim-backend.onrender.com";

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 180000,
  headers: { "Content-Type": "application/json" },
});

// ── Token helpers ─────────────────────────────────────────────────────────────

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setTokens(access_token: string, refresh_token: string): void {
  localStorage.setItem("access_token", access_token);
  localStorage.setItem("refresh_token", refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

// ── Request interceptor — attach Bearer token ─────────────────────────────────

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Response interceptor — silent token refresh on 401 ───────────────────────

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const isUnauthorized = error.response?.status === 401;
    const isRefreshEndpoint = error.config?.url?.includes("/auth/refresh");

    if (isUnauthorized && !isRefreshEndpoint && typeof window !== "undefined") {
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token: new_refresh } = res.data;
          // Rotate both tokens
          setTokens(access_token, new_refresh ?? refreshToken);

          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`;
            return api.request(error.config);
          }
        } catch {
          clearTokens();
          window.location.href = "/auth/login";
        }
      } else {
        // No refresh token at all — send to login
        window.location.href = "/auth/login";
      }
    }

    return Promise.reject(error);
  }
);

// ── Auth API ──────────────────────────────────────────────────────────────────

export const authApi = {
  /**
   * Register, persist tokens immediately, then fetch /me.
   * Tokens are in localStorage before /me fires → no 401.
   */
  register: async (data: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
  }) => {
    const res = await api.post("/auth/register", data);
    // Persist tokens BEFORE calling /me so the request interceptor picks them up
    setTokens(res.data.access_token, res.data.refresh_token);
    return res;
  },

  /**
   * Login, persist tokens immediately, then let the caller fetch /me.
   */
  login: async (email: string, password: string) => {
    const form = new FormData();
    form.append("username", email);
    form.append("password", password);
    const res = await api.post("/auth/login", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    setTokens(res.data.access_token, res.data.refresh_token);
    return res;
  },

  me: () => api.get("/auth/me"),

  logout: () => {
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
  }) => api.post("/analysis/audit-rejection", data),

  scanCIS: (documentId: string) => api.post(`/analysis/scan-cis/${documentId}`),

  portabilityGuide: (data: {
    policy_document_id: string;
    years_covered: number;
    reason_for_porting: string;
  }) => api.post("/analysis/portability-guide", data),

  edaakhilGuide: () => api.get("/analysis/edaakhil-guide"),
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
};

// ── Claims API ────────────────────────────────────────────────────────────────

export const claimsApi = {
  list: () => api.get("/claims/"),
  get: (id: string) => api.get(`/claims/${id}`),
};