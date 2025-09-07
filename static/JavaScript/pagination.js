const logContainer = document.querySelector(".log-container");
const cards = Array.from(document.querySelectorAll(".log-card"));
const pagination = document.querySelector(".pagination");

function setupPagination() {
    pagination.innerHTML = "";

    const header = document.querySelector(".card-header");
    const containerStyle = getComputedStyle(logContainer);

    const containerPaddingTop = parseFloat(containerStyle.paddingTop);
    const containerPaddingBottom = parseFloat(containerStyle.paddingBottom);

    const headerBottom = header.getBoundingClientRect().bottom + window.scrollY;
    const paginationTop = pagination.getBoundingClientRect().top + window.scrollY;

    const availableHeight = paginationTop - headerBottom - containerPaddingTop - containerPaddingBottom;

    const gap = parseFloat(containerStyle.gap) || 0;
    const baseHeight = cards[0]?.offsetHeight || 100;

    let cardsPerPage = Math.floor((availableHeight + gap) / (baseHeight + gap));
    cardsPerPage = Math.max(1, cardsPerPage) - 1;

    const totalGapSpace = gap * (cardsPerPage);
    const cardHeight = (availableHeight - totalGapSpace) / cardsPerPage;

    const totalPages = Math.ceil(cards.length / cardsPerPage);

    function showPage(page) {
        cards.forEach(card => (card.style.display = "none"));

        const start = page * cardsPerPage;
        const end = start + cardsPerPage;
        const currentCards = cards.slice(start, end);

        currentCards.forEach(card => (card.style.display = "flex"));

        if (page === totalPages - 1) {
            logContainer.classList.remove("space-between");
            logContainer.classList.add("no-space");
        } else {
            logContainer.classList.remove("no-space");
            logContainer.classList.add("space-between");
        }

        logContainer.style.overflowY = "hidden";

        pagination.querySelectorAll("span").forEach((btn, idx) => {
            btn.classList.toggle("active", idx === page);
        });
    }

    for (let i = 0; i < totalPages; i++) {
        const span = document.createElement("span");
        span.textContent = i + 1;
        span.addEventListener("click", () => showPage(i));
        pagination.appendChild(span);
    }

    showPage(0);
}

document.addEventListener("click", e => {
    const card = e.target.closest(".log-card");
    if (!card) return;

    const isExpanded = card.classList.toggle("expanded");

    card.style.height = isExpanded ? "auto" : "";
    const anyExpanded = cards.some(c => c.classList.contains("expanded"));
    logContainer.style.overflowY = anyExpanded ? "auto" : "hidden";
});

window.addEventListener("resize", setupPagination);
window.addEventListener("load", setupPagination);