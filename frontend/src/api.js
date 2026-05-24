const DEFAULT_TIMEOUT_MS = 120000;

export async function apiFetch(path, options = {}) {
  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api';
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs || DEFAULT_TIMEOUT_MS);

  try {
    return await fetch(`${apiBase}${path}`, {
      ...options,
      signal: controller.signal,
    });
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error('Request timed out. The backend may be waking up or processing a large resume. Please try again in a minute.');
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

