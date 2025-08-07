document.addEventListener("DOMContentLoaded", function () {
    const loginForm = document.getElementById("loginForm");

    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const formData = new FormData(loginForm);
        const data = {
        username: formData.get("username"),
        password: formData.get("password")
        };

        try {
        const response = await fetch("/validateLogin", {
            method: "POST",
            headers: {
            "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        const status = document.getElementById("loginStatus");
        console.log(result.status)
        if (result.status === 'success') {
            status.textContent = "Login successful!";
            status.style.color = "green";
            window.location.href = "/launchDashboard";
        } else {
            status.textContent = result.message || "Login failed";
            status.style.color = "red";
        }
        } catch (err) {
        console.error("Error:", err);
        document.getElementById("loginStatus").textContent = "An error occurred";
        }
    });
});