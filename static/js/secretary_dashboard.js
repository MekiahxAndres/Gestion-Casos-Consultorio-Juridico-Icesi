const categoriesScript = document.getElementById("categories-data");
const categoriesData = categoriesScript ? JSON.parse(categoriesScript.textContent) : [];

function openCategoriesModal() {
    const modal = document.getElementById("categoriesModal");
    const content = document.getElementById("categoriesContent");
    showCategoriesView(content);
    modal.classList.add("active");
}

function showCategoriesView(content) {
    let html = "";

    categoriesData.forEach(category => {
        html += `
            <div class="category-item">
                <div class="category-header" onclick="toggleCategoryExpand(this)">
                    <span class="category-toggle">›</span>
                    <span class="category-title">${category.label}</span>
                    <span class="category-count">${category.count}</span>
                </div>

                <div class="category-types">
        `;

        category.types.forEach(type => {
            html += `
                    <a href="javascript:void(0);" onclick="showFilteredCasesView('${category.key}', '${type.code}', '${category.label}', '${type.label}')" class="type-item">
                        <span class="type-name">• ${type.label}</span>
                        <span class="type-count">${type.count}</span>
                    </a>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    content.innerHTML = html;
}

function showFilteredCasesView(categoryCode, typeCode, categoryLabel, typeLabel) {
    const content = document.getElementById("categoriesContent");

    fetch(`/cases/api/casos/asignados/?category=${encodeURIComponent(categoryCode)}&type=${encodeURIComponent(typeCode)}`)
        .then(response => response.json())
        .then(data => {
            let html = `
                <div style="margin-bottom: 16px;">
                    <button onclick="backToCategoriesView()" class="back-link" style="border: none; background: none; cursor: pointer; padding: 0;">← Volver a salas</button>

                    <h3 style="font-size: 18px; font-weight: 700; color: #1a1a1a; margin: 16px 0 4px 0;">Casos de ${categoryLabel}</h3>
                    <p style="font-size: 14px; color: #666; margin: 0 0 16px 0;">Trámite: ${typeLabel}</p>
                </div>
            `;

            if (data.cases.length > 0) {
                html += '<div style="display: flex; flex-direction: column; gap: 12px;">';

                data.cases.forEach(caseItem => {
                    html += `
                        <a href="/cases/casos/${caseItem.id}/" class="case-card">
                            <div style="font-size: 16px; font-weight: 700; color: #7c6fd9; margin-bottom: 8px;">${caseItem.case_number}</div>
                            <div style="font-size: 13px; font-weight: 600; color: #1a1a1a; margin-bottom: 6px;">${caseItem.beneficiary_name}</div>
                            <div style="font-size: 12px; color: #666; margin-bottom: 4px;"><strong>Estudiante:</strong> ${caseItem.student_name}</div>
                            <div style="font-size: 12px; color: #666;"><strong>Estado:</strong> ${caseItem.status}</div>
                        </a>
                    `;
                });

                html += "</div>";
            } else {
                html += `
                    <div style="text-align: center; padding: 40px 24px;">
                        <i class="fa-solid fa-magnifying-glass" style="font-size: 42px; color: #5b5ce2; margin-bottom: 12px;"></i>
                        <div style="font-size: 16px; font-weight: 700; color: #1a1a1a;">No hay casos en esta sala</div>
                    </div>
                `;
            }

            content.innerHTML = html;
        })
        .catch(error => {
            console.error("Error:", error);
            content.innerHTML = "<p>Error al cargar los casos</p>";
        });
}

function backToCategoriesView() {
    const content = document.getElementById("categoriesContent");
    showCategoriesView(content);
}

function closeCategoriesModal() {
    const modal = document.getElementById("categoriesModal");
    modal.classList.remove("active");
}

function toggleCategoryExpand(headerElement) {
    const typesContainer = headerElement.nextElementSibling;
    const toggleIcon = headerElement.querySelector(".category-toggle");

    typesContainer.classList.toggle("expanded");
    toggleIcon.classList.toggle("expanded");
}

const categoriesModal = document.getElementById("categoriesModal");
if (categoriesModal) {
    categoriesModal.addEventListener("click", function (e) {
        if (e.target === this) {
            closeCategoriesModal();
        }
    });
}

function toggleDropdown() {
    const dropdown = document.getElementById("userDropdown");
    if (dropdown) {
        dropdown.classList.toggle("open");
    }
}

window.addEventListener("click", function (event) {
    if (
        !event.target.closest(".user-trigger") &&
        !event.target.closest(".dropdown-menu")
    ) {
        const dropdown = document.getElementById("userDropdown");
        if (dropdown) {
            dropdown.classList.remove("open");
        }
    }
});
