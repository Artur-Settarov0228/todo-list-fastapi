const AUTH_KEY = "educrm_auth_token";
const USER_KEY = "educrm_auth_user";

function getToken() {
  return localStorage.getItem(AUTH_KEY);
}

function getUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (_error) {
    return null;
  }
}

function setAuth(token, user) {
  localStorage.setItem(AUTH_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(USER_KEY);
}

async function apiRequest(url, options = {}) {
  const token = getToken();
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    let detail = "Request failed.";
    try {
      const data = await response.json();
      detail = data.detail || detail;
    } catch (_error) {
      detail = response.statusText || detail;
    }
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

function setMessage(element, message, isError = true) {
  element.textContent = message;
  element.classList.toggle("is-success", !isError && Boolean(message));
}

if (window.location.pathname === "/") {
  const storedUser = getUser();
  if (getToken() && storedUser) {
    window.location.href = "/dashboard";
  }

  const loginFormEl = document.getElementById("login-form");
  const registerFormEl = document.getElementById("register-form");
  const loginMessageEl = document.getElementById("login-message");
  const registerMessageEl = document.getElementById("register-message");
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const target = button.dataset.tabTarget;
      tabButtons.forEach((item) => item.classList.toggle("is-active", item === button));
      tabPanels.forEach((panel) =>
        panel.classList.toggle("is-active", panel.dataset.tabPanel === target),
      );
    });
  });

  loginFormEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(loginMessageEl, "");
    const payload = {
      role: document.getElementById("login-role").value,
      username: document.getElementById("login-username").value.trim().toLowerCase(),
      password: document.getElementById("login-password").value,
    };

    try {
      const data = await apiRequest("/api/login", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setAuth(data.token, data.user);
      window.location.href = "/dashboard";
    } catch (error) {
      setMessage(loginMessageEl, error.message);
    }
  });

  registerFormEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(registerMessageEl, "");
    const payload = {
      full_name: document.getElementById("register-full-name").value.trim(),
      role: document.getElementById("register-role").value,
      username: document.getElementById("register-username").value.trim().toLowerCase(),
      password: document.getElementById("register-password").value,
    };

    try {
      await apiRequest("/api/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      registerFormEl.reset();
      setMessage(registerMessageEl, "Registration successful. You can log in now.", false);
      document.querySelector('[data-tab-target="login"]').click();
    } catch (error) {
      setMessage(registerMessageEl, error.message);
    }
  });
}
