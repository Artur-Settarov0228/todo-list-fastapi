const AUTH_KEY = "todo_auth_token";
const USERNAME_KEY = "todo_auth_username";

function getToken() {
  return localStorage.getItem(AUTH_KEY);
}

function getUsername() {
  return localStorage.getItem(USERNAME_KEY);
}

function setAuth(token, username) {
  localStorage.setItem(AUTH_KEY, token);
  localStorage.setItem(USERNAME_KEY, username);
}

function clearAuth() {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(USERNAME_KEY);
}

async function apiRequest(url, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let detail = "Server xatoligi";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch (error) {
      console.error(error);
    }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}
