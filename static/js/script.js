const API = "/api";

let dashboardData = null;


// DATE

document.getElementById("current-date").textContent =
    new Date().toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric"
    });


// API HELPER

async function apiRequest(url, method = "GET", data = null) {

    const options = {
        method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(API + url, options);

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.error || "Something went wrong.");
    }

    return result;
}


// LOAD DASHBOARD

async function loadDashboard() {

    try {

        dashboardData = await apiRequest("/dashboard");

        updateStats();
        renderHabits();
        renderGarden();
        renderPlants();
        renderAchievements();
        renderStatistics();

    } catch (error) {
        alert(error.message);
    }
}


// UPDATE STATISTICS

function updateStats() {

    const data = dashboardData;

    document.getElementById("completed-count").textContent =
        `${data.completed} / ${data.total}`;

    document.getElementById("streak-count").textContent =
        `${data.streak} days`;

    document.getElementById("seed-count").textContent =
        `${data.seeds} Seeds`;

    document.getElementById("total-seeds").textContent =
        data.seeds;

    const percentage = data.total === 0
        ? 0
        : Math.round((data.completed / data.total) * 100);

    document.getElementById("progress-text").textContent =
        `${percentage}% completed`;
}


// RENDER HABITS

function renderHabits() {

    const dashboard = document.getElementById("dashboard-habits");
    const allHabits = document.getElementById("all-habits");

    dashboard.innerHTML = "";
    allHabits.innerHTML = "";

    if (dashboardData.habits.length === 0) {

        dashboard.innerHTML = "<p>No habits yet. Add your first habit!</p>";
        allHabits.innerHTML = "<p>Your garden is waiting for its first seed 🌱</p>";

        return;
    }

    dashboardData.habits.forEach(habit => {

        dashboard.appendChild(createHabitElement(habit, false));

        allHabits.appendChild(createHabitElement(habit, true));

    });
}


// CREATE HABIT ELEMENT

function createHabitElement(habit, showActions) {

    const item = document.createElement("div");
    item.className = "habit-item";

    const icon = document.createElement("div");
    icon.className = "habit-icon";
    icon.textContent = habit.icon;

    const info = document.createElement("div");
    info.className = "habit-info";

    const title = document.createElement("h3");
    title.textContent = habit.name;

    const description = document.createElement("p");
    description.textContent = habit.description || "Your little goal";

    info.append(title, description);

    const actions = document.createElement("div");
    actions.className = "habit-actions";

    const complete = document.createElement("button");

    complete.className = "complete-btn";

    if (habit.completed) {
        complete.classList.add("done");
        complete.textContent = "✓ Done";
    } else {
        complete.textContent = "Complete";
    }

    complete.onclick = () => toggleHabit(habit);

    actions.appendChild(complete);

    if (showActions) {

        const edit = document.createElement("button");

        edit.className = "small-btn";
        edit.textContent = "✏️";

        edit.onclick = () => editHabit(habit);

        const remove = document.createElement("button");

        remove.className = "small-btn delete-btn";
        remove.textContent = "🗑️";

        remove.onclick = () => deleteHabit(habit.id);

        actions.append(edit, remove);
    }

    item.append(icon, info, actions);

    return item;
}


// COMPLETE OR UNDO HABIT

async function toggleHabit(habit) {

    try {

        if (habit.completed) {

            if (!confirm("Undo this completion? You will lose 10 seeds.")) {
                return;
            }

            await apiRequest(
                `/habits/${habit.id}/complete`,
                "DELETE"
            );

        } else {

            await apiRequest(
                `/habits/${habit.id}/complete`,
                "POST"
            );

        }

        await loadDashboard();

    } catch (error) {
        alert(error.message);
    }
}


// ADD HABIT

document.getElementById("habit-form").addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const name = document.getElementById("habit-name").value.trim();

        const description =
            document.getElementById("habit-description").value.trim();

        if (!name) return;

        try {

            await apiRequest("/habits", "POST", {
                name,
                description,
                icon: "🌱"
            });

            this.reset();

            await loadDashboard();

            alert("Your new habit has been planted! 🌱");

        } catch (error) {
            alert(error.message);
        }

    }
);


// EDIT HABIT

async function editHabit(habit) {

    const name = prompt("Enter new habit name:", habit.name);

    if (name === null) return;

    const description = prompt(
        "Enter new description:",
        habit.description || ""
    );

    if (description === null) return;

    try {

        await apiRequest(
            `/habits/${habit.id}`,
            "PUT",
            {
                name,
                description
            }
        );

        await loadDashboard();

    } catch (error) {
        alert(error.message);
    }
}


// DELETE HABIT

async function deleteHabit(id) {

    if (!confirm("Are you sure you want to delete this habit?")) {
        return;
    }

    try {

        await apiRequest(`/habits/${id}`, "DELETE");

        await loadDashboard();

    } catch (error) {
        alert(error.message);
    }
}


// GARDEN GROWTH

function renderGarden() {

    const garden = document.getElementById("garden-plants");
    garden.innerHTML = "";

    const stages = [
        ["🌱"],
        ["🌱", "🌿"],
        ["🌿", "🌷", "🌱"],
        ["🌻", "🌷", "🌿", "🌷"],
        ["🌸", "🌻", "🌷", "🌻", "🌸"]
    ];

    const total = dashboardData.total;
    const completed = dashboardData.completed;

    const percentage = total === 0
        ? 0
        : completed / total;

    const stage = total === 0
        ? 0
        : Math.min(4, Math.floor(percentage * 4));

    const plants = stages[stage];

    plants.forEach(plant => {

        const span = document.createElement("span");

        span.className = "growing-plant";
        span.textContent = plant;

        garden.appendChild(span);

    });
}


// MY PLANTS

function renderPlants() {

    const container = document.getElementById("my-plants");
    const shop = document.getElementById("plant-shop");

    container.innerHTML = "";
    shop.innerHTML = "";

    if (dashboardData.plants.length === 0) {
        container.innerHTML = "<p>Your garden is waiting for its first plant! 🌱</p>";
    }

    dashboardData.plants.forEach(plant => {

        const card = document.createElement("div");

        card.className = "plant-card";

        card.innerHTML = `
            <span>${plant.emoji}</span>
            <h3></h3>
            <p>Growing in your garden</p>
        `;

        card.querySelector("h3").textContent = plant.name;

        container.appendChild(card);

    });


    dashboardData.shop.forEach(plant => {

        const card = document.createElement("div");

        card.className = "plant-card";

        card.innerHTML = `
            <span>${plant.emoji}</span>
            <h3></h3>
            <p>🌰 ${plant.cost} seeds</p>
            <button class="primary-btn">Buy Plant</button>
        `;

        card.querySelector("h3").textContent = plant.name;

        card.querySelector("button").onclick = () => buyPlant(plant.id);

        shop.appendChild(card);

    });

}


// BUY PLANT

async function buyPlant(id) {

    try {

        await apiRequest(`/plants/${id}/buy`, "POST");

        await loadDashboard();

        alert("Your new plant is ready! 🌷");

    } catch (error) {
        alert(error.message);
    }
}


// ACHIEVEMENTS

function renderAchievements() {

    const container =
        document.getElementById("achievement-list");

    container.innerHTML = "";

    dashboardData.achievements.forEach(achievement => {

        const card = document.createElement("div");

        card.className = "achievement-card";

        if (!achievement.unlocked) {
            card.classList.add("locked");
        }

        card.innerHTML = `
            <span>${achievement.emoji}</span>
            <h3></h3>
            <p></p>
            <strong>${achievement.unlocked ? "Unlocked ✓" : "Locked 🔒"}</strong>
        `;

        card.querySelector("h3").textContent = achievement.name;
        card.querySelector("p").textContent = achievement.description;

        container.appendChild(card);

    });

}


// WEEKLY STATISTICS

function renderStatistics() {

    const container =
        document.getElementById("weekly-chart");

    container.innerHTML = "";

    const max = Math.max(
        1,
        ...dashboardData.weekly.map(day => day.count)
    );

    dashboardData.weekly.forEach(day => {

        const column = document.createElement("div");

        column.className = "chart-column";

        const percentage = (day.count / max) * 100;

        column.innerHTML = `
            <small>${day.count}</small>
            <div class="bar" style="height:${percentage}%"></div>
            <span>${day.day}</span>
        `;

        container.appendChild(column);

    });

}


// NAVIGATION

document.querySelectorAll(".nav-item").forEach(button => {

    button.addEventListener("click", () => {

        document.querySelectorAll(".nav-item").forEach(item => {
            item.classList.remove("active");
        });

        document.querySelectorAll(".page").forEach(page => {
            page.classList.remove("active");
        });

        button.classList.add("active");

        document.getElementById(
            button.dataset.page
        ).classList.add("active");

    });

});


// START APPLICATION

loadDashboard();