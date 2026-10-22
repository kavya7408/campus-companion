
const API_URL = "/api";

// ================================
// 1. GET HTML ELEMENTS
// ================================

const taskForm = document.getElementById("task-form");
const taskInput = document.getElementById("task-input");
const taskList = document.getElementById("task-list");
const emptyTasks = document.getElementById("empty-tasks");
const taskCount = document.getElementById("task-count");
const completedCount = document.getElementById("completed-count");

const plannerForm = document.getElementById("planner-form");
const studySubject = document.getElementById("study-subject");
const studyTime = document.getElementById("study-time");
const studyList = document.getElementById("study-list");
const emptyStudy = document.getElementById("empty-study");
const studyCount = document.getElementById("study-count");

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");

// ================================
// 2. STORE APPLICATION DATA
// ================================

let tasks = [];
let backendStudySessions = [];

// Load saved manual sessions safely.
function getSavedStudySessions() {
    try {
        const saved = localStorage.getItem("campusStudySessions");
        const sessions = saved ? JSON.parse(saved) : [];

        return Array.isArray(sessions) ? sessions : [];
    } catch (error) {
        console.error("Could not read saved study sessions:", error);
        return [];
    }
}

let studySessions = getSavedStudySessions();

// Save manual sessions whenever they change.
function saveStudySessions() {
    try {
        localStorage.setItem(
            "campusStudySessions",
            JSON.stringify(studySessions)
        );
    } catch (error) {
        console.error("Could not save study sessions:", error);
        alert("Your browser could not save the study sessions.");
    }
}

// ================================
// 3. LOAD TASKS FROM FLASK
// ================================

async function loadTasks() {
    try {
        const response = await fetch(`${API_URL}/tasks`);
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error("Could not load tasks.");
        }

        tasks = data.tasks.map(function (task) {
            return {
                id: task.id,
                name: task.title,
                completed: task.status === "completed"
            };
        });

        renderTasks();
    } catch (error) {
        console.error("Loading tasks failed:", error);
    }
}

// ================================
// 4. DISPLAY TASKS
// ================================

function renderTasks() {
    if (!taskList || !emptyTasks) return;

    taskList.innerHTML = "";

    tasks.forEach(function (task) {
        const item = document.createElement("li");
        const checkbox = document.createElement("input");
        const taskText = document.createElement("span");
        const deleteButton = document.createElement("button");

        checkbox.type = "checkbox";
        checkbox.checked = task.completed;
        checkbox.setAttribute(
            "aria-label",
            "Mark " + task.name + " as completed"
        );

        taskText.textContent = task.name;

        if (task.completed) {
            taskText.style.textDecoration = "line-through";
        }

        checkbox.addEventListener("change", async function () {
            try {
                const response = await fetch(
                    `${API_URL}/tasks/${task.id}`,
                    {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            status: checkbox.checked
                                ? "completed"
                                : "pending"
                        })
                    }
                );

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error("Could not update task.");
                }

                await loadTasks();
                await loadBackendStudyPlan();
            } catch (error) {
                console.error("Updating task failed:", error);
                alert("Could not update the task. Please try again.");
                await loadTasks();
            }
        });

        deleteButton.type = "button";
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", async function () {
            try {
                const response = await fetch(
                    `${API_URL}/tasks/${task.id}`,
                    { method: "DELETE" }
                );

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error("Could not delete task.");
                }

                await loadTasks();
                await loadBackendStudyPlan();
            } catch (error) {
                console.error("Deleting task failed:", error);
                alert("Could not delete the task. Please try again.");
            }
        });

        item.appendChild(checkbox);
        item.appendChild(taskText);
        item.appendChild(deleteButton);
        taskList.appendChild(item);
    });

    emptyTasks.style.display = tasks.length === 0 ? "block" : "none";

    const completed = tasks.filter(function (task) {
        return task.completed;
    }).length;

    const pending = tasks.length - completed;

    if (taskCount) {
        taskCount.textContent =
            pending + (pending === 1 ? " task" : " tasks");
    }

    if (completedCount) {
        completedCount.textContent =
            completed + (completed === 1 ? " task" : " tasks");
    }
}

// ================================
// 5. ADD TASKS
// ================================

if (taskForm && taskInput) {
    taskForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const title = taskInput.value.trim();

        if (!title) return;

        const today = new Date().toLocaleDateString("en-CA");

        try {
            const response = await fetch(`${API_URL}/tasks`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    title: title,
                    task_type: "other",
                    due_date: today,
                    estimated_hours: 1,
                    priority: "medium"
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.message || "Could not add task.");
            }

            taskInput.value = "";

            await loadTasks();
            await loadBackendStudyPlan();
        } catch (error) {
            console.error("Adding task failed:", error);
            alert("Could not add the task. Check that Flask is running.");
        }
    });
}

// ================================
// 6. DISPLAY STUDY SESSIONS
// ================================

function renderStudySessions() {
    if (!studyList || !emptyStudy) return;

    studyList.innerHTML = "";

    // Display manually added sessions.
    studySessions.forEach(function (session, index) {
        const item = document.createElement("li");
        const sessionText = document.createElement("span");
        const deleteButton = document.createElement("button");

        sessionText.textContent =
            session.subject + " — " + session.duration + " minutes";

        deleteButton.type = "button";
        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", function () {
            studySessions.splice(index, 1);

            saveStudySessions();
            renderStudySessions();
        });

        item.appendChild(sessionText);
        item.appendChild(deleteButton);
        studyList.appendChild(item);
    });

    // Display sessions generated by the Flask backend.
    backendStudySessions.forEach(function (session) {
        const item = document.createElement("li");

        item.textContent =
            session.task + " — " +
            session.hours + " hour(s) (" +
            session.date + ")";

        studyList.appendChild(item);
    });

    const totalSessions =
        studySessions.length + backendStudySessions.length;

    emptyStudy.style.display =
        totalSessions === 0 ? "block" : "none";

    if (studyCount) {
        studyCount.textContent =
            totalSessions +
            (totalSessions === 1
                ? " study session planned"
                : " study sessions planned");
    }
}

// ================================
// 7. ADD MANUAL STUDY SESSIONS
// ================================

if (plannerForm && studySubject && studyTime) {
    plannerForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const subject = studySubject.value.trim();
        const duration = Number(studyTime.value);

        if (!subject || !Number.isFinite(duration) || duration <= 0) {
            return;
        }

        studySessions.push({
            subject: subject,
            duration: duration
        });

        // Save immediately before rendering.
        saveStudySessions();

        studySubject.value = "";
        renderStudySessions();
    });
}

// ================================
// 8. LOAD STUDY PLAN FROM FLASK
// ================================

async function loadBackendStudyPlan() {
    try {
        const response = await fetch(
            `${API_URL}/study-plan?daily_hours=3&session_hours=2`
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error("Could not load the backend study plan.");
        }

        backendStudySessions = [];

        if (Array.isArray(data.schedule)) {
            data.schedule.forEach(function (day) {
                if (Array.isArray(day.sessions)) {
                    day.sessions.forEach(function (session) {
                        backendStudySessions.push(session);
                    });
                }
            });
        }

        renderStudySessions();
    } catch (error) {
        console.error("Loading study plan failed:", error);

        // Manual sessions remain visible even if Flask is unavailable.
        renderStudySessions();
    }
}

// ================================
// 9. AI ASSISTANT
// ================================

function addMessage(message, className) {
    if (!chatMessages) return;

    const messageElement = document.createElement("div");
    messageElement.className = className;
    messageElement.textContent = message;

    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

if (chatForm && chatInput && chatMessages) {
    chatForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const message = chatInput.value.trim();

        if (!message) return;

        addMessage(message, "user-message");
        chatInput.value = "";

        try {
            const response = await fetch(`${API_URL}/parse-message`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: message
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(
                    data.message || "Could not process your message."
                );
            }

            addMessage(
                data.message ||
                "Your message was processed. Check My Tasks for saved tasks.",
                "bot-message"
            );

            await loadTasks();
            await loadBackendStudyPlan();
        } catch (error) {
            console.error("Assistant error:", error);

            addMessage(
                "I couldn't process your message. Please check that Flask is running and try again.",
                "bot-message"
            );
        }
    });
}

// ================================
// 10. START THE APPLICATION
// ================================

renderTasks();
renderStudySessions();

loadTasks();
loadBackendStudyPlan();
