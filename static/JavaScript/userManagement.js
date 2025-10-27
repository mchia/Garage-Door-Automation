document.addEventListener("DOMContentLoaded", function () {
    /**
     * Generic form submit handler
     * @param {string} formId - The ID of the form
     * @param {string} url - The endpoint to POST to
     */
    function handleFormSubmit(formId, url) {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener("submit", async function (e) {
            e.preventDefault();

            const formData = new FormData(form);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            try {
                const response = await fetch(url, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data)
                });

                const result = await response.json();
            } catch (err) {
                console.error("Error:", err);
                const statusEl = document.getElementById("loginStatus");
                if (statusEl) statusEl.textContent = "An error occurred";
            }
        });
    }

    handleFormSubmit("addUser", "/addUser");
    handleFormSubmit("removeUser", "/removeUser");
});