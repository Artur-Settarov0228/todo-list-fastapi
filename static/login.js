const loginFormEl = document.getElementById("login-form");
const loginMessageEl = document.getElementById("message");

if (getToken()) {
  window.location.href = "/tasks";
}

loginFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("username").value.trim().toLowerCase();
  const password = document.getElementById("password").value;
  loginMessageEl.textContent = "";

  try {
    const data = await apiRequest("/api/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setAuth(data.token, data.username);
    window.location.href = "/tasks";
  } catch (error) {
    loginMessageEl.textContent = error.message;
  }
});
