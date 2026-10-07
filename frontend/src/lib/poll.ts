import { documentsApi } from "@/lib/api";

export interface PollHandle { cancel: () => void }

/**
 * Poll a document's processing status safely:
 *  - one request at a time (no overlapping requests when the server is slow),
 *  - gentle backoff (3s -> 10s) so a long OCR job is not hammered,
 *  - stops on auth errors, on completion/failure, after `maxMs`, or when cancelled
 *    (call cancel() from a useEffect cleanup).
 * Uses the lightweight /status endpoint, then fetches the full document once when done.
 */
export function pollDocument(
  docId: string,
  cb: {
    onDone: (doc: any) => void;
    onFailed: () => void;
    onTimeout?: () => void;
    onAuthError?: () => void;
  },
  maxMs = 10 * 60 * 1000,
): PollHandle {
  let cancelled = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const started = Date.now();
  let delay = 3000;

  const tick = async () => {
    if (cancelled) return;
    if (Date.now() - started > maxMs) { cb.onTimeout?.(); return; }
    try {
      const st = (await documentsApi.status(docId)).data;
      if (cancelled) return;
      if (st.ocr_status === "done") {
        const full = await documentsApi.get(docId);
        if (!cancelled) cb.onDone(full.data);
        return;
      }
      if (st.ocr_status === "failed") { cb.onFailed(); return; }
    } catch (e: any) {
      if (e?.response?.status === 401) { cb.onAuthError?.(); return; }
      // transient error: keep polling with backoff
    }
    delay = Math.min(delay * 1.3, 10000);
    timer = setTimeout(tick, delay);
  };

  timer = setTimeout(tick, delay);
  return { cancel: () => { cancelled = true; if (timer) clearTimeout(timer); } };
}
