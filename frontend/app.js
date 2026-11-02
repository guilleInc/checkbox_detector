(() => {
  const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
  const ALLOWED_TYPES = ["image/png", "image/jpeg"];
  const ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg"];
  const MIN_ZOOM = 0.1;
  const MAX_ZOOM = 8;
  const ZOOM_STEP = 1.25;
  const COLORS = { checked: "#1a7f37", unchecked: "#cf222e" };

  const $ = (id) => document.getElementById(id);
  const dropZone = $("drop-zone");
  const fileInput = $("file-input");
  const fileBar = $("file-bar");
  const detectButton = $("detect-button");
  const changeButton = $("change-button");
  const removeButton = $("remove-button");
  const statusEl = $("status");
  const errorEl = $("error");
  const summaryEl = $("summary");
  const emptyState = $("empty-state");
  const viewerEl = $("viewer");
  const viewport = $("viewport");
  const stage = $("stage");
  const preview = $("preview");
  const overlay = $("overlay");
  const zoomLevel = $("zoom-level");

  let selectedFile = null;
  let objectUrl = null;
  let boxes = [];
  let zoom = 1;
  let busy = false;

  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = !message;
  }

  function setBusy(value, message = "") {
    busy = value;
    detectButton.disabled = value;
    changeButton.disabled = value;
    removeButton.disabled = value;
    statusEl.textContent = message;
    statusEl.classList.toggle("loading", value);
  }

  function formatSize(bytes) {
    return bytes < 1024 * 1024
      ? `${Math.max(1, Math.round(bytes / 1024))} KB`
      : `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function isSupported(file) {
    const name = file.name.toLowerCase();
    return ALLOWED_TYPES.includes(file.type)
      || (!file.type && ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension)));
  }

  function resetResults() {
    boxes = [];
    summaryEl.hidden = true;
    overlay.getContext("2d").clearRect(0, 0, overlay.width, overlay.height);
  }

  function showImageControls(visible) {
    dropZone.hidden = visible;
    fileBar.hidden = !visible;
    viewerEl.hidden = !visible;
    emptyState.hidden = visible;
  }

  function removeFile() {
    if (busy) return;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = null;
    selectedFile = null;
    preview.onload = preview.onerror = null;
    preview.removeAttribute("src");
    resetResults();
    showError("");
    showImageControls(false);
  }

  function selectFile(file) {
    if (!file || busy) return;
    showError("");
    if (!isSupported(file)) {
      showError("Unsupported file type. Please select a PNG, JPG or JPEG image.");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      showError("The image is larger than the 10 MiB limit.");
      return;
    }

    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    selectedFile = file;
    resetResults();
    $("file-name").textContent = file.name;
    $("file-size").textContent = formatSize(file.size);
    preview.onload = () => {
      overlay.width = preview.naturalWidth;
      overlay.height = preview.naturalHeight;
      showImageControls(true);
      fitToWidth();
    };
    preview.onerror = () => {
      removeFile();
      showError("The selected file could not be displayed as an image.");
    };
    preview.src = objectUrl;
  }

  function applyZoom(value, anchor) {
    if (!preview.naturalWidth) return;
    const previous = zoom;
    zoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, value));
    stage.style.width = `${preview.naturalWidth * zoom}px`;
    stage.style.height = `${preview.naturalHeight * zoom}px`;
    zoomLevel.textContent = `${Math.round(zoom * 100)}%`;
    if (anchor) {
      // Keep the image point under the cursor fixed while zooming.
      const ratio = zoom / previous;
      viewport.scrollLeft = (viewport.scrollLeft + anchor.x) * ratio - anchor.x;
      viewport.scrollTop = (viewport.scrollTop + anchor.y) * ratio - anchor.y;
    }
  }

  function fitToWidth() {
    const available = viewport.clientWidth;
    applyZoom(available > 0 ? Math.min(1, available / preview.naturalWidth) : 1);
  }

  function draw() {
    const context = overlay.getContext("2d");
    context.clearRect(0, 0, overlay.width, overlay.height);
    context.lineWidth = Math.max(2, Math.round(Math.max(overlay.width, overlay.height) / 400));
    for (const box of boxes) {
      const [x1, y1, x2, y2] = box.bbox;
      context.strokeStyle = box.is_checked ? COLORS.checked : COLORS.unchecked;
      context.strokeRect(x1, y1, x2 - x1 + 1, y2 - y1 + 1);
    }
  }

  function showSummary() {
    const checked = boxes.filter((box) => box.is_checked).length;
    $("total-count").textContent = boxes.length;
    $("checked-count").textContent = checked;
    $("unchecked-count").textContent = boxes.length - checked;
    summaryEl.hidden = false;
  }

  async function errorMessage(response) {
    try {
      const body = await response.json();
      if (typeof body.detail === "string") return body.detail;
    } catch (_) { /* fall through to the generic message */ }
    return `Detection failed (HTTP ${response.status}).`;
  }

  async function detect() {
    if (!selectedFile || busy) return;
    showError("");
    resetResults();
    setBusy(true, "Detecting checkboxes…");
    try {
      const body = new FormData();
      body.append("file", selectedFile);
      const response = await fetch("/detect", { method: "POST", body });
      if (!response.ok) {
        showError(await errorMessage(response));
        return;
      }
      const result = await response.json();
      boxes = Array.isArray(result.boxes) ? result.boxes : [];
      draw();
      showSummary();
    } catch (_) {
      showError("Could not reach the detection service. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  function enableDrop(element) {
    element.addEventListener("dragover", (event) => {
      event.preventDefault();
      element.classList.add("dragover");
    });
    element.addEventListener("dragleave", () => element.classList.remove("dragover"));
    element.addEventListener("drop", (event) => {
      event.preventDefault();
      element.classList.remove("dragover");
      const files = event.dataTransfer.files;
      if (files.length > 1) {
        showError("Please drop a single image.");
        return;
      }
      selectFile(files[0]);
    });
  }

  fileInput.addEventListener("change", () => {
    selectFile(fileInput.files[0]);
    fileInput.value = "";
  });
  dropZone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      fileInput.click();
    }
  });
  enableDrop(dropZone);
  enableDrop(fileBar);
  // Prevent the browser from navigating to a file dropped outside the drop zone.
  for (const type of ["dragover", "drop"]) {
    window.addEventListener(type, (event) => event.preventDefault());
  }

  detectButton.addEventListener("click", detect);
  changeButton.addEventListener("click", () => fileInput.click());
  removeButton.addEventListener("click", removeFile);
  $("zoom-in").addEventListener("click", () => applyZoom(zoom * ZOOM_STEP));
  $("zoom-out").addEventListener("click", () => applyZoom(zoom / ZOOM_STEP));
  $("zoom-fit").addEventListener("click", fitToWidth);
  $("zoom-actual").addEventListener("click", () => applyZoom(1));
  viewport.addEventListener("wheel", (event) => {
    if (!event.ctrlKey && !event.metaKey) return;
    event.preventDefault();
    const rect = viewport.getBoundingClientRect();
    const anchor = { x: event.clientX - rect.left, y: event.clientY - rect.top };
    applyZoom(zoom * (event.deltaY < 0 ? ZOOM_STEP : 1 / ZOOM_STEP), anchor);
  }, { passive: false });
})();
