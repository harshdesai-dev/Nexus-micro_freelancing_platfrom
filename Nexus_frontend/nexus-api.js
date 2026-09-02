/* Shared HTTP client for the static NEXUS frontend. */
(() => {
  class NexusApiError extends Error {
    constructor(message, { status = 0, code = 'REQUEST_FAILED', details = null } = {}) {
      super(message || 'The request could not be completed.');
      this.name = 'NexusApiError';
      this.status = status;
      this.code = code;
      this.details = details;
    }
  }

  const configuredBaseUrl = () => {
    const meta = document.querySelector('meta[name="nexus-api-base-url"]');
    const configured = window.NEXUS_CONFIG && window.NEXUS_CONFIG.API_BASE_URL;
    return String(configured || (meta && meta.content) || location.origin).replace(/\/$/, '');
  };

  const buildUrl = path => `${configuredBaseUrl()}${path.startsWith('/') ? path : `/${path}`}`;

  async function request(path, options = {}) {
    const {
      method = 'GET', body, headers = {}, token, retryOnUnauthorized = true,
      skipAuth = false, signal
    } = options;
    const requestHeaders = { Accept: 'application/json', ...headers };
    const isFormData = body instanceof FormData;
    if (body !== undefined && body !== null && !isFormData && !requestHeaders['Content-Type']) {
      requestHeaders['Content-Type'] = 'application/json';
    }
    const accessToken = token || (!skipAuth && window.NexusAuth && window.NexusAuth.getAccessToken());
    if (accessToken) requestHeaders.Authorization = `Bearer ${accessToken}`;

    let response;
    try {
      response = await fetch(buildUrl(path), {
        method,
        headers: requestHeaders,
        body: body === undefined || body === null ? undefined : (isFormData ? body : JSON.stringify(body)),
        signal
      });
    } catch (_) {
      throw new NexusApiError('Unable to reach the NEXUS service. Please check your connection and try again.');
    }

    let payload = null;
    try { payload = await response.json(); } catch (_) { /* A non-JSON response is handled below. */ }
    if (response.status === 401 && retryOnUnauthorized && !skipAuth && window.NexusAuth) {
      const refreshed = await window.NexusAuth.refreshAccessToken();
      if (refreshed) return request(path, { ...options, retryOnUnauthorized: false });
    }
    if (!response.ok || !payload || payload.success !== true) {
      const error = payload && payload.error;
      throw new NexusApiError(
        (error && error.message) || (payload && payload.message) || `Request failed (${response.status || 'network error'}).`,
        { status: response.status, code: (error && error.code) || 'REQUEST_FAILED', details: error || null }
      );
    }
    return payload.data;
  }

  window.NexusApi = Object.freeze({
    request,
    get: (path, options) => request(path, { ...options, method: 'GET' }),
    post: (path, body, options) => request(path, { ...options, method: 'POST', body }),
    put: (path, body, options) => request(path, { ...options, method: 'PUT', body }),
    patch: (path, body, options) => request(path, { ...options, method: 'PATCH', body }),
    Error: NexusApiError,
    getBaseUrl: configuredBaseUrl
  });
})();
