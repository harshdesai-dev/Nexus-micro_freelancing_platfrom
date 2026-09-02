/* Central JWT session state for the static NEXUS frontend. */
(() => {
  const STORAGE_KEY = 'nexus.auth.session.v1';
  let state = { user: null, accessToken: null, refreshToken: null, restored: false };
  let refreshPromise = null;

  function save() {
    if (!state.accessToken || !state.refreshToken) return clearStorage();
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ user: state.user, accessToken: state.accessToken, refreshToken: state.refreshToken }));
  }
  function clearStorage() { localStorage.removeItem(STORAGE_KEY); }
  function hydrate() {
    try {
      const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (stored && stored.accessToken && stored.refreshToken) state = { ...state, ...stored };
    } catch (_) { clearStorage(); }
  }
  function setSession(data) {
    if (!data || !data.user || !data.tokens || !data.tokens.access || !data.tokens.refresh) {
      throw new NexusApi.Error('The server returned an incomplete authentication session.');
    }
    state = { ...state, user: data.user, accessToken: data.tokens.access, refreshToken: data.tokens.refresh };
    save();
    return state.user;
  }
  function clearSession() {
    state = { user: null, accessToken: null, refreshToken: null, restored: true };
    clearStorage();
  }
  async function refreshAccessToken() {
    if (!state.refreshToken) return false;
    if (refreshPromise) return refreshPromise;
    refreshPromise = NexusApi.post('/api/auth/refresh', { refresh: state.refreshToken }, { skipAuth: true, retryOnUnauthorized: false })
      .then(data => {
        if (!data || !data.access) throw new NexusApi.Error('The server did not return a refreshed session.');
        state.accessToken = data.access;
        save();
        return true;
      })
      .catch(() => { clearSession(); return false; })
      .finally(() => { refreshPromise = null; });
    return refreshPromise;
  }
  async function restore() {
    if (state.restored) return state.user;
    hydrate();
    state.restored = true;
    if (!state.accessToken) return null;
    try {
      const data = await NexusApi.get('/api/auth/me');
      state.user = data.user;
      save();
      return state.user;
    } catch (_) {
      clearSession();
      return null;
    }
  }
  async function login(credentials) {
    const data = await NexusApi.post('/api/auth/login', credentials, { skipAuth: true, retryOnUnauthorized: false });
    return setSession(data);
  }
  async function register(payload) {
    const data = await NexusApi.post('/api/auth/register', payload, { skipAuth: true, retryOnUnauthorized: false });
    return setSession(data);
  }
  async function logout() {
    const refresh = state.refreshToken;
    try {
      if (refresh) await NexusApi.post('/api/auth/logout', { refresh }, { retryOnUnauthorized: false });
    } finally { clearSession(); }
  }
  function hasRole(...roles) { return Boolean(state.user && roles.includes(state.user.role)); }

  window.NexusAuth = Object.freeze({
    login, register, logout, restore, refreshAccessToken, hasRole,
    getAccessToken: () => state.accessToken,
    getUser: () => state.user,
    getState: () => ({ user: state.user, role: state.user && state.user.role, authenticated: Boolean(state.accessToken && state.user) })
  });
})();
