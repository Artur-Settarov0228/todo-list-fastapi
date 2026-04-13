const taskFormEl = document.getElementById("task-form");
const taskInputEl = document.getElementById("task-input");
const helloTextEl = document.getElementById("hello-text");
const logoutBtnEl = document.getElementById("logout-btn");

const lists = {
  open: document.getElementById("list-open"),
  in_progress: document.getElementById("list-in-progress"),
  done: document.getElementById("list-done"),
};

const statusOptions = [
  { value: "open", label: "Ochiq" },
  { value: "in_progress", label: "Bajarilmoqda" },
  { value: "done", label: "Bajarib bo'ldi" },
];

if (!getToken()) {
  window.location.href = "/";
}

helloTextEl.textContent = `${getUsername() || "User"} tasklari`;

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderEmpty(listEl, text) {
  listEl.innerHTML = `<li class="empty">${escapeHtml(text)}</li>`;
}

function taskItemHtml(task) {
  const options = statusOptions
    .map((item) => {
      const selected = item.value === task.status ? "selected" : "";
      return `<option value="${item.value}" ${selected}>${item.label}</option>`;
    })
    .join("");

  return `
    <li class="todo-item ${task.status === "done" ? "done" : ""}" data-id="${task.id}">
      <p>${escapeHtml(task.text)}</p>
      <div class="task-actions">
        <select data-action="status">${options}</select>
        <button type="button" data-action="delete">Ochirish</button>
      </div>
    </li>
  `;
}

function renderTasks(tasks) {
  const grouped = {
    open: [],
    in_progress: [],
    done: [],
  };
  tasks.forEach((task) => {
    if (grouped[task.status]) grouped[task.status].push(task);
  });

  Object.entries(lists).forEach(([status, listEl]) => {
    const values = grouped[status];
    if (!values.length) {
      renderEmpty(listEl, "Hozircha yo'q");
      return;
    }
    listEl.innerHTML = values.map(taskItemHtml).join("");
  });
}

async function loadTasks() {
  try {
    const tasks = await apiRequest("/api/todos");
    renderTasks(tasks);
  } catch (error) {
    if (error.message.toLowerCase().includes("token") || error.message.includes("401")) {
      clearAuth();
      window.location.href = "/";
      return;
    }
    Object.values(lists).forEach((listEl) => renderEmpty(listEl, error.message));
  }
}

taskFormEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = taskInputEl.value.trim();
  if (!text) return;

  try {
    await apiRequest("/api/todos", {
      method: "POST",
      body: JSON.stringify({ text, status: "open" }),
    });
    taskInputEl.value = "";
    await loadTasks();
  } catch (error) {
    alert(error.message);
  }
});

Object.values(lists).forEach((listEl) => {
  listEl.addEventListener("click", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (!target.matches('button[data-action="delete"]')) return;

    const item = target.closest(".todo-item");
    if (!item) return;
    const todoId = Number(item.dataset.id);
    if (!todoId) return;

    try {
      await apiRequest(`/api/todos/${todoId}`, { method: "DELETE" });
      await loadTasks();
    } catch (error) {
      alert(error.message);
    }
  });

  listEl.addEventListener("change", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLSelectElement)) return;
    if (!target.matches('select[data-action="status"]')) return;

    const item = target.closest(".todo-item");
    if (!item) return;
    const todoId = Number(item.dataset.id);
    if (!todoId) return;

    try {
      await apiRequest(`/api/todos/${todoId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: target.value }),
      });
      await loadTasks();
    } catch (error) {
      alert(error.message);
    }
  });
});

logoutBtnEl.addEventListener("click", async () => {
  try {
    await apiRequest("/api/logout", { method: "POST" });
  } catch (error) {
    console.error(error);
  } finally {
    clearAuth();
    window.location.href = "/";
  }
});

loadTasks();
