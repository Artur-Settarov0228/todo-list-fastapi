const listEl = document.getElementById("todo-list");
const formEl = document.getElementById("todo-form");
const inputEl = document.getElementById("todo-input");

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

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

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

function renderTodos(todos) {
  if (!todos.length) {
    listEl.innerHTML = '<li class="empty">Hozircha vazifalar yo\'q</li>';
    return;
  }

  listEl.innerHTML = todos
    .map(
      (todo) => `
        <li class="todo-item ${todo.done ? "done" : ""}" data-id="${todo.id}">
          <input type="checkbox" ${todo.done ? "checked" : ""} />
          <p>${escapeHtml(todo.text)}</p>
          <button type="button" data-action="delete">Ochirish</button>
        </li>
      `
    )
    .join("");
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadTodos() {
  const todos = await request("/api/todos");
  renderTodos(todos);
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  try {
    await request("/api/todos", {
      method: "POST",
      body: JSON.stringify({ text }),
    });
    inputEl.value = "";
    await loadTodos();
  } catch (error) {
    alert(error.message);
  }
});

listEl.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;

  const item = target.closest(".todo-item");
  if (!item) return;
  const todoId = Number(item.dataset.id);
  if (!todoId) return;

  if (target.matches('button[data-action="delete"]')) {
    try {
      await request(`/api/todos/${todoId}`, { method: "DELETE" });
      await loadTodos();
    } catch (error) {
      alert(error.message);
    }
  }
});

listEl.addEventListener("change", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLInputElement) || target.type !== "checkbox") return;

  const item = target.closest(".todo-item");
  if (!item) return;
  const todoId = Number(item.dataset.id);
  if (!todoId) return;

  try {
    await request(`/api/todos/${todoId}`, {
      method: "PATCH",
      body: JSON.stringify({ done: target.checked }),
    });
    await loadTodos();
  } catch (error) {
    alert(error.message);
  }
});

loadTodos().catch((error) => {
  listEl.innerHTML = `<li class="empty">${escapeHtml(error.message)}</li>`;
});
