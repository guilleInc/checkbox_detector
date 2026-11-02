import { STATUS_LABELS } from "./status.js";

// List of loaded images: click one to select it, or its ✕ to remove it.
export function createGallery({ onSelect, onRemove }) {
  const thumbsEl = document.getElementById("thumbs");
  const countEl = document.getElementById("gallery-count");
  const sectionEl = document.getElementById("gallery");

  function createThumb(item, index, isActive) {
    const li = document.createElement("li");
    li.className = isActive ? "thumb active" : "thumb";

    const select = document.createElement("button");
    select.type = "button";
    select.className = "thumb-select";
    select.title = item.file.name;
    if (isActive) select.setAttribute("aria-current", "true");
    const image = new Image();
    image.src = item.url;
    image.alt = "";
    const name = document.createElement("span");
    name.className = "thumb-name";
    name.textContent = item.file.name;
    const status = document.createElement("span");
    status.className = `status ${item.status}`;
    status.textContent = STATUS_LABELS[item.status];
    select.append(image, name, status);
    select.addEventListener("click", () => onSelect(index));

    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "thumb-remove";
    remove.textContent = "✕";
    remove.setAttribute("aria-label", `Remove ${item.file.name}`);
    remove.addEventListener("click", () => onRemove(index));

    li.append(select, remove);
    return li;
  }

  function render(items, activeIndex) {
    countEl.textContent = items.length;
    sectionEl.hidden = items.length === 0;
    thumbsEl.replaceChildren(
      ...items.map((item, index) => createThumb(item, index, index === activeIndex)),
    );
  }

  return { render };
}
