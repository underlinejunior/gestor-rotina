
(function () {
    "use strict";

    function t(v) {
        return (v || "").replace(/\s+/g, " ").trim().toLowerCase();
    }

    function classifyAction(link, index) {
        const href = (link.getAttribute("href") || "").toLowerCase();
        const icon = (link.querySelector("i")?.className || "").toLowerCase();
        const text = t(link.textContent);

        const rules = [
            {
                match: /hoje|taref|miss|minhas-tarefas|enviar-foto/.test(href + " " + text) || /check|ui-checks-grid/.test(icon),
                label: "Hoje",
                cls: "child-unified-action--today"
            },
            {
                match: /histor|clock/.test(href + " " + text) || /clock-history/.test(icon),
                label: "Histórico",
                cls: "child-unified-action--history"
            },
            {
                match: /habil|skill|graph|painel/.test(href + " " + text) || /graph-up-arrow/.test(icon),
                label: "Skills",
                cls: "child-unified-action--skills"
            },
            {
                match: /conquist|trophy|trophy/.test(href + " " + text) || /trophy/.test(icon),
                label: "Conquistas",
                cls: "child-unified-action--achievements"
            },
            {
                match: /relat|pdf|file|semanal/.test(href + " " + text) || /file|filetype-pdf/.test(icon),
                label: "Relatório",
                cls: "child-unified-action--report"
            },
            {
                match: /edit|editar|pencil/.test(href + " " + text) || /pencil/.test(icon),
                label: "Editar",
                cls: "child-unified-action--edit"
            }
        ];

        for (const rule of rules) {
            if (rule.match) return rule;
        }

        const fallback = [
            {label: "Hoje", cls: "child-unified-action--today"},
            {label: "Histórico", cls: "child-unified-action--history"},
            {label: "Skills", cls: "child-unified-action--skills"},
            {label: "Conquistas", cls: "child-unified-action--achievements"},
            {label: "Relatório", cls: "child-unified-action--report"},
            {label: "Editar", cls: "child-unified-action--edit"}
        ];

        return fallback[index] || {label: "Ação", cls: "child-unified-action--edit"};
    }

    function fixChildrenCards() {
        const cards = Array.from(document.querySelectorAll(".child-unified-card, .child-card, article, .card, .content-card"));

        cards.forEach((card) => {
            const possibleActions = Array.from(card.querySelectorAll("a, button")).filter((el) => el.querySelector("i, svg"));
            if (possibleActions.length < 4 || possibleActions.length > 7) return;

            // Find action container: parent having 4-7 direct action children.
            let actionContainer = null;
            for (const box of card.querySelectorAll("div, nav, section")) {
                const direct = Array.from(box.children).filter((el) => ["A", "BUTTON"].includes(el.tagName));
                if (direct.length >= 4 && direct.length <= 7) {
                    actionContainer = box;
                    break;
                }
            }
            if (!actionContainer) return;

            const actionItems = Array.from(actionContainer.children).filter((el) => ["A", "BUTTON"].includes(el.tagName));
            if (actionItems.length < 4) return;

            // Identify main info container: largest textual sibling or first non-actions block.
            const parent = actionContainer.parentElement;
            if (!parent) return;

            parent.classList.add("child-unified-card__body");

            if (actionContainer.parentElement === parent) {
                actionContainer.classList.add("child-unified-card__actions");
                // Move actions below all siblings.
                parent.appendChild(actionContainer);
            }

            actionItems.forEach((item, idx) => {
                const meta = classifyAction(item, idx);
                item.classList.add("child-unified-action", meta.cls);

                // Clean previous content into icon + label.
                const icon = item.querySelector("i, svg");
                let iconWrap = item.querySelector(".child-unified-action__icon");
                if (!iconWrap) {
                    iconWrap = document.createElement("span");
                    iconWrap.className = "child-unified-action__icon";
                    if (icon) {
                        icon.parentNode.insertBefore(iconWrap, icon);
                        iconWrap.appendChild(icon);
                    } else {
                        iconWrap.textContent = "•";
                    }
                    item.prepend(iconWrap);
                }

                let label = item.querySelector(".child-unified-action__label");
                if (!label) {
                    label = document.createElement("span");
                    label.className = "child-unified-action__label";
                    item.appendChild(label);
                }
                label.textContent = meta.label;

                Array.from(item.childNodes).forEach((node) => {
                    if (node.nodeType === Node.TEXT_NODE) node.textContent = "";
                });

                item.setAttribute("title", meta.label);
                item.setAttribute("aria-label", meta.label);
            });
        });
    }

    document.addEventListener("DOMContentLoaded", fixChildrenCards);
})();
