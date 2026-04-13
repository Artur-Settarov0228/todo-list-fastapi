const registerFormEl = document.getElementById("register-form");
const registerMessageEl = document.getElementById("message");

if (getToken()) {
  window.location.href = "/tasks";
}

registerFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = document.getElementById("username").value.trim().toLowerCase();
  const password = document.getElementById("password").value;
  registerMessageEl.textContent = "";

  try {
    await apiRequest("/api/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    registerMessageEl.textContent = "Registratsiya bo'ldi. Endi login qiling.";
    registerFormEl.reset();
  } catch (error) {
    registerMessageEl.textContent = error.message;
  }
});
