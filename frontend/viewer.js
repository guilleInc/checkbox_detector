
const MIN_ZOOM = 0.1;
const MAX_ZOOM = 8;
const ZOOM_STEP = 1.25;
const COLORS = { checked: "#1a7f37", unchecked: "#cf222e" };

// Shows one image with its title, detect button, summary, zoom and click-and-drag panning.
export function createViewer({ onDetect, onImageError }) {
  const $ = (id) => document.getElementById(id);
  const sectionEl = $("viewer");
  const titleEl = $("viewer-title");
  const detectButton = $("detect-button");
  const errorEl = $("detect-error");
  const summaryEl = $("summary");
  const viewport = $("viewport");
  const stage = $("stage");
  const preview = $("preview");
  const overlay = $("overlay");
  const zoomLevel = $("zoom-level");

  let current = null;
  let zoom = 1;

  function applyZoom(value) {
    if (!preview.naturalWidth) return;
    zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));
    stage.style.width = `${preview.naturalWidth * zoom}px`;
    stage.style.height = `${preview.naturalHeight * zoom}px`;
    zoomLevel.textContent = `${Math.round(zoom * 100)}%`;
  }

  function fitToWidth() {
    const available = viewport.clientWidth;
    applyZoom(available > 0 ? Math.min(1, available / preview.naturalWidth) : 1);
  }

  function drawResults() {
    const context = overlay.getContext("2d");
    context.clearRect(0, 0, overlay.width, overlay.height);
    const boxes = current && current.boxes;
    summaryEl.hidden = !boxes;
    if (!boxes) return;

    context.lineWidth = Math.max(2, Math.round(Math.max(overlay.width, overlay.height) / 400));
    for (const box of boxes) {
      const [x1, y1, x2, y2] = box.bbox;
      context.strokeStyle = box.is_checked ? COLORS.checked : COLORS.unchecked;
      context.strokeRect(x1, y1, x2 - x1 + 1, y2 - y1 + 1);
    }
    const checked = boxes.filter((box) => box.is_checked).length;
    $("total-count").textContent = boxes.length;
    $("checked-count").textContent = checked;
    $("unchecked-count").textContent = boxes.length - checked;
  }

  // Renders the given item, or the empty state when item is null.
  function render(item) {
    current = item;
    sectionEl.hidden = !item;
    if (!item) {
      preview.removeAttribute("src");
      delete preview.dataset.url;
      titleEl.textContent = "";
      return;
    }

    titleEl.textContent = item.file.name;
    const detecting = item.status === "detecting";
    detectButton.disabled = detecting;
    detectButton.textContent = detecting ? "Detecting…" : "Detect checkboxes";
    errorEl.textContent = item.error;
    errorEl.hidden = !item.error;

    if (preview.dataset.url === item.url) {
      drawResults();
    } else {
      // The load handler sizes the canvas and draws the results once the image is ready.
      overlay.getContext("2d").clearRect(0, 0, overlay.width, overlay.height);
      summaryEl.hidden = true;
      preview.dataset.url = item.url;
      preview.src = item.url;
    }
  }

  preview.addEventListener("load", () => {
    overlay.width = preview.naturalWidth;
    overlay.height = preview.naturalHeight;
    fitToWidth();
    drawResults();
  });
  preview.addEventListener("error", () => current && onImageError(current));

  detectButton.addEventListener("click", () => current && onDetect(current));
  $("zoom-in").addEventListener("click", () => applyZoom(zoom * ZOOM_STEP));
  $("zoom-out").addEventListener("click", () => applyZoom(zoom / ZOOM_STEP));
  $("zoom-fit").addEventListener("click", fitToWidth);

  // Click-and-drag panning: scroll the viewport by the mouse movement.
  let lastX = 0;
  let lastY = 0;
  let panning = false;
  viewport.addEventListener("mousedown", (event) => {
    if (event.button !== 0) return;
    event.preventDefault();
    panning = true;
    lastX = event.clientX;
    lastY = event.clientY;
    viewport.classList.add("panning");
  });
  window.addEventListener("mousemove", (event) => {
    if (!panning) return;
    viewport.scrollLeft -= event.clientX - lastX;
    viewport.scrollTop -= event.clientY - lastY;
    lastX = event.clientX;
    lastY = event.clientY;
  });
  window.addEventListener("mouseup", () => {
    panning = false;
    viewport.classList.remove("panning");
  });

  return { render };
}
