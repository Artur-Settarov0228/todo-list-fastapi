const user = getUser();

if (window.location.pathname === "/dashboard") {
  if (!getToken() || !user) {
    clearAuth();
    window.location.href = "/";
  }
}

const escapeHtml = (text = "") =>
  String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

function formatResultPercent(item) {
  if (!item.total_questions) return "0%";
  return `${Math.round((item.score / item.total_questions) * 100)}%`;
}

function showEmpty(container, text) {
  container.innerHTML = `<div class="empty-state">${escapeHtml(text)}</div>`;
}

function statCard(label, value) {
  return `
    <article class="stat-card">
      <p>${escapeHtml(label)}</p>
      <strong>${escapeHtml(value)}</strong>
    </article>
  `;
}

function subjectCard(subject) {
  return `
    <article class="subject-card" style="--subject-color: ${escapeHtml(subject.color)}">
      <div class="subject-badge">${escapeHtml(subject.name)}</div>
      <h3>${escapeHtml(subject.name)}</h3>
      <p>${escapeHtml(subject.description)}</p>
      <div class="subject-meta">
        <span>${subject.lesson_count} lessons</span>
        <span>${subject.quiz_count} quizzes</span>
      </div>
    </article>
  `;
}

function announcementCard(item) {
  return `
    <article class="stack-card">
      <div class="card-row">
        <h3>${escapeHtml(item.title)}</h3>
        <span class="pill">${escapeHtml(item.audience)}</span>
      </div>
      <p>${escapeHtml(item.body)}</p>
      <small>By ${escapeHtml(item.author_name)} on ${escapeHtml(item.created_at)}</small>
    </article>
  `;
}

function lessonCard(item) {
  return `
    <article class="lesson-card">
      <div class="card-row">
        <h3>${escapeHtml(item.title)}</h3>
        <span class="subject-chip" style="--subject-color: ${escapeHtml(item.subject.color)}">
          ${escapeHtml(item.subject.name)}
        </span>
      </div>
      <p class="lesson-summary">${escapeHtml(item.summary)}</p>
      <p>${escapeHtml(item.content)}</p>
      <small>By ${escapeHtml(item.teacher_name)} on ${escapeHtml(item.created_at)}</small>
    </article>
  `;
}

function quizCard(quiz, currentRole) {
  const questionsHtml = quiz.questions
    .map((question, index) => {
      const optionsHtml = Object.entries(question.options)
        .map(([key, label]) => {
          const disabled = currentRole !== "student" ? "disabled" : "";
          return `
            <label class="option-line">
              <input type="radio" name="question-${question.id}" value="${key}" ${disabled} />
              <span>${key}. ${escapeHtml(label)}</span>
            </label>
          `;
        })
        .join("");

      const answerHint =
        currentRole === "student"
          ? ""
          : `<p class="answer-hint">Correct answer: ${escapeHtml(question.correct_option)}</p>`;

      return `
        <div class="quiz-question" data-question-id="${question.id}">
          <p><strong>Q${index + 1}.</strong> ${escapeHtml(question.question_text)}</p>
          <div class="option-list">${optionsHtml}</div>
          ${answerHint}
        </div>
      `;
    })
    .join("");

  const action =
    currentRole === "student"
      ? `<button class="quiz-submit-btn" type="button" data-quiz-submit="${quiz.id}">Submit Quiz</button>`
      : `<p class="info-note">Teachers and admins can review quiz content here.</p>`;

  return `
    <article class="stack-card quiz-card" data-quiz-id="${quiz.id}">
      <div class="card-row">
        <div>
          <h3>${escapeHtml(quiz.title)}</h3>
          <p class="microcopy">${escapeHtml(quiz.subject.name)} • ${quiz.question_count} questions</p>
        </div>
        <span class="subject-chip" style="--subject-color: ${escapeHtml(quiz.subject.color)}">
          ${escapeHtml(quiz.subject.name)}
        </span>
      </div>
      <p>${escapeHtml(quiz.description)}</p>
      <div class="quiz-questions">${questionsHtml}</div>
      <div class="quiz-action">
        ${action}
        <p class="quiz-feedback" data-quiz-feedback="${quiz.id}"></p>
      </div>
    </article>
  `;
}

function resultCard(item, currentRole) {
  const studentLine =
    currentRole === "student" ? "" : `<p>Student: ${escapeHtml(item.student_name)}</p>`;
  return `
    <article class="stack-card">
      <h3>${escapeHtml(item.quiz_title)}</h3>
      <p>${escapeHtml(item.subject_name)} • Score ${item.score}/${item.total_questions} (${formatResultPercent(item)})</p>
      ${studentLine}
      <small>${escapeHtml(item.submitted_at)}</small>
    </article>
  `;
}

function userCard(item) {
  return `
    <article class="stack-card">
      <div class="card-row">
        <h3>${escapeHtml(item.full_name)}</h3>
        <span class="pill">${escapeHtml(item.role)}</span>
      </div>
      <p>${escapeHtml(item.username)}</p>
      <small>Joined ${escapeHtml(item.created_at)}</small>
    </article>
  `;
}

function teacherSubjectCard(item) {
  return `
    <article class="stack-card compact-card">
      <div class="card-row">
        <h3>${escapeHtml(item.name)}</h3>
        <span class="subject-chip" style="--subject-color: ${escapeHtml(item.color)}">
          Assigned
        </span>
      </div>
    </article>
  `;
}

function collectQuizAnswers(card) {
  const answers = {};
  card.querySelectorAll(".quiz-question").forEach((questionEl) => {
    const questionId = Number(questionEl.dataset.questionId);
    const checked = questionEl.querySelector("input[type='radio']:checked");
    if (questionId && checked instanceof HTMLInputElement) {
      answers[questionId] = checked.value;
    }
  });
  return answers;
}

async function loadDashboard() {
  const welcomeTitle = document.getElementById("welcome-title");
  const welcomeSubtitle = document.getElementById("welcome-subtitle");
  const roleBadge = document.getElementById("role-badge");
  const statsGrid = document.getElementById("stats-grid");
  const subjectsGrid = document.getElementById("subjects-grid");
  const announcementsList = document.getElementById("announcements-list");
  const lessonsList = document.getElementById("lessons-list");
  const quizList = document.getElementById("quiz-list");
  const resultsList = document.getElementById("results-list");
  const usersPanel = document.getElementById("users-panel");
  const usersList = document.getElementById("users-list");
  const announcementPanel = document.getElementById("announcement-panel");
  const teacherPanel = document.getElementById("teacher-panel");
  const teacherSubjectsList = document.getElementById("teacher-subjects");
  const lessonForm = document.getElementById("lesson-form");
  const lessonSubject = document.getElementById("lesson-subject");
  const lessonsTitle = document.getElementById("lessons-title");
  const resultsTitle = document.getElementById("results-title");

  try {
    const data = await apiRequest("/api/bootstrap");
    setAuth(getToken(), data.user);

    welcomeTitle.textContent = `${data.user.full_name}'s workspace`;
    welcomeSubtitle.textContent = `Logged in as ${data.user.role}.`;
    roleBadge.textContent = data.user.role;

    const visibleStats = [
      ["Users", data.stats.users],
      ["Teachers", data.stats.teachers],
      ["Students", data.stats.students],
      ["Quizzes", data.stats.quizzes],
      ["Attempts", data.stats.attempts],
    ];
    statsGrid.innerHTML = visibleStats.map(([label, value]) => statCard(label, String(value))).join("");

    subjectsGrid.innerHTML = data.subjects.map(subjectCard).join("");
    announcementsList.innerHTML = data.announcements.length
      ? data.announcements.map(announcementCard).join("")
      : "";
    if (!data.announcements.length) showEmpty(announcementsList, "No announcements yet.");

    lessonsList.innerHTML = data.lessons.length ? data.lessons.map(lessonCard).join("") : "";
    if (!data.lessons.length) showEmpty(lessonsList, "No lessons available right now.");

    quizList.innerHTML = data.quizzes.length
      ? data.quizzes.map((quiz) => quizCard(quiz, data.user.role)).join("")
      : "";
    if (!data.quizzes.length) showEmpty(quizList, "No quizzes available.");

    resultsList.innerHTML = data.results.length
      ? data.results.map((item) => resultCard(item, data.user.role)).join("")
      : "";
    if (!data.results.length) showEmpty(resultsList, "No quiz results yet.");

    if (data.user.role === "admin") {
      usersPanel.classList.remove("hidden");
      announcementPanel.classList.remove("hidden");
      usersList.innerHTML = data.users.map(userCard).join("");
      lessonsTitle.textContent = "All published lessons";
      resultsTitle.textContent = "Platform performance";
    }

    if (data.user.role === "teacher") {
      teacherPanel.classList.remove("hidden");
      lessonForm.classList.remove("hidden");
      teacherSubjectsList.innerHTML = data.teacher_subjects.length
        ? data.teacher_subjects.map(teacherSubjectCard).join("")
        : "";
      if (!data.teacher_subjects.length) {
        showEmpty(teacherSubjectsList, "No subjects assigned.");
      }

      lessonSubject.innerHTML = data.teacher_subjects
        .map((subject) => `<option value="${subject.id}">${escapeHtml(subject.name)}</option>`)
        .join("");
      lessonsTitle.textContent = "Your lessons";
      resultsTitle.textContent = "Student quiz performance";
    }

    if (data.user.role === "student") {
      resultsTitle.textContent = "Your quiz history";
    }
  } catch (error) {
    if (error.message.toLowerCase().includes("session") || error.message.includes("Authentication")) {
      clearAuth();
      window.location.href = "/";
      return;
    }
    document.body.innerHTML = `<main class="page"><section class="card"><p>${escapeHtml(error.message)}</p></section></main>`;
  }
}

document.getElementById("logout-btn")?.addEventListener("click", async () => {
  try {
    await apiRequest("/api/logout", { method: "POST" });
  } catch (_error) {
    // Ignore logout cleanup errors.
  } finally {
    clearAuth();
    window.location.href = "/";
  }
});

document.getElementById("announcement-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const messageEl = document.getElementById("announcement-message");
  setMessage(messageEl, "");
  const payload = {
    title: document.getElementById("announcement-title").value.trim(),
    audience: document.getElementById("announcement-audience").value,
    body: document.getElementById("announcement-body").value.trim(),
  };

  try {
    await apiRequest("/api/announcements", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    event.target.reset();
    setMessage(messageEl, "Announcement published.", false);
    await loadDashboard();
  } catch (error) {
    setMessage(messageEl, error.message);
  }
});

document.getElementById("lesson-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const messageEl = document.getElementById("lesson-message");
  setMessage(messageEl, "");
  const payload = {
    subject_id: Number(document.getElementById("lesson-subject").value),
    title: document.getElementById("lesson-title").value.trim(),
    summary: document.getElementById("lesson-summary").value.trim(),
    content: document.getElementById("lesson-content").value.trim(),
  };

  try {
    await apiRequest("/api/lessons", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    event.target.reset();
    setMessage(messageEl, "Lesson published successfully.", false);
    await loadDashboard();
  } catch (error) {
    setMessage(messageEl, error.message);
  }
});

document.getElementById("quiz-list")?.addEventListener("click", async (event) => {
  const target = event.target;
  if (!(target instanceof HTMLElement)) return;
  const quizId = Number(target.dataset.quizSubmit);
  if (!quizId) return;

  const card = target.closest(".quiz-card");
  const feedbackEl = document.querySelector(`[data-quiz-feedback="${quizId}"]`);
  if (!card || !feedbackEl) return;
  setMessage(feedbackEl, "");

  const answers = collectQuizAnswers(card);
  const questionCount = card.querySelectorAll(".quiz-question").length;
  if (Object.keys(answers).length !== questionCount) {
    setMessage(feedbackEl, "Answer every question before submitting.");
    return;
  }

  try {
    const result = await apiRequest(`/api/quizzes/${quizId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    });
    setMessage(
      feedbackEl,
      `Submitted: ${result.score}/${result.total_questions} (${result.percentage}%).`,
      false,
    );
    await loadDashboard();
  } catch (error) {
    setMessage(feedbackEl, error.message);
  }
});

if (window.location.pathname === "/dashboard") {
  loadDashboard();
}
