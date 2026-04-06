const goalInput = document.getElementById("goalInput");
const difficultyInput = document.getElementById("difficultyInput");
const createGoalBtn = document.getElementById("createGoalBtn");
const messageEl = document.getElementById("message");
const goalsListEl = document.getElementById("goalsList");

function setMessage(text = "") {
  messageEl.textContent = text;
}

function formatDate(isoString) {
  if (!isoString) return "";
  return new Date(isoString).toLocaleString();
}

function escapeHtml(str) {
  return str
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function fetchGoals() {
  const res = await fetch("/api/goals");
  if (!res.ok) throw new Error("Failed to load goals");
  return res.json();
}

async function createGoal(title, difficulty) {
  const res = await fetch("/api/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, difficulty }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Create failed" }));
    throw new Error(err.detail || "Create failed");
  }

  return res.json();
}

async function completeQuest(questId) {
  const res = await fetch(`/api/quests/${questId}/complete`, {
    method: "PATCH",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Complete failed" }));
    throw new Error(err.detail || "Complete failed");
  }

  return res.json();
}

async function nextQuest(goalId, difficulty) {
  const res = await fetch(`/api/goals/${goalId}/next-quest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ difficulty }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Generation failed" }));
    throw new Error(err.detail || "Generation failed");
  }

  return res.json();
}

function renderGoals(goals) {
  if (!goals.length) {
    goalsListEl.innerHTML = "<p>No goals yet. Create your first quest above.</p>";
    return;
  }

  goalsListEl.innerHTML = goals
    .map((goal) => {
      const questsHtml = goal.quests
        .map(
          (quest) => `
          <article class="quest">
            <p>${escapeHtml(quest.text)}</p>
            <div class="quest-meta">
              <div class="badge-wrap">
                <span class="badge ${quest.status}">${quest.status}</span>
                <span class="badge difficulty">${quest.difficulty}</span>
              </div>
              <small>${formatDate(quest.created_at)}</small>
              ${
                quest.status === "pending"
                  ? `<button data-complete-id="${quest.id}" class="secondary">Complete</button>`
                  : `<small>Completed: ${formatDate(quest.completed_at)}</small>`
              }
            </div>
          </article>
        `
        )
        .join("");

      return `
        <section class="goal">
          <h3 class="goal-title">${escapeHtml(goal.title)}</h3>
          <div>${questsHtml || "<p>No quests yet.</p>"}</div>
          <div class="next-quest-row">
            <select data-next-difficulty-id="${goal.id}">
              <option value="easy">Easy</option>
              <option value="medium" selected>Medium</option>
              <option value="hard">Hard</option>
            </select>
            <button data-next-goal-id="${goal.id}">Generate next quest</button>
          </div>
        </section>
      `;
    })
    .join("");

  goalsListEl.querySelectorAll("button[data-complete-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.dataset.completeId);
      btn.disabled = true;
      try {
        await completeQuest(id);
        await loadAndRenderGoals();
      } catch (err) {
        setMessage(err.message || "Unable to complete quest");
      } finally {
        btn.disabled = false;
      }
    });
  });

  goalsListEl.querySelectorAll("button[data-next-goal-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = Number(btn.dataset.nextGoalId);
      const selector = goalsListEl.querySelector(`select[data-next-difficulty-id="${id}"]`);
      const difficulty = selector ? selector.value : "medium";
      btn.disabled = true;
      try {
        await nextQuest(id, difficulty);
        await loadAndRenderGoals();
      } catch (err) {
        setMessage(err.message || "Unable to generate next quest");
      } finally {
        btn.disabled = false;
      }
    });
  });
}

async function loadAndRenderGoals() {
  setMessage("");
  try {
    const goals = await fetchGoals();
    renderGoals(goals);
  } catch (err) {
    setMessage(err.message || "Could not load goals");
  }
}

createGoalBtn.addEventListener("click", async () => {
  const title = goalInput.value.trim();
  const difficulty = difficultyInput.value;
  if (!title) {
    setMessage("Please enter a study goal.");
    return;
  }

  createGoalBtn.disabled = true;
  setMessage("");

  try {
    await createGoal(title, difficulty);
    goalInput.value = "";
    difficultyInput.value = "medium";
    await loadAndRenderGoals();
  } catch (err) {
    setMessage(err.message || "Could not create quest");
  } finally {
    createGoalBtn.disabled = false;
  }
});

loadAndRenderGoals();
