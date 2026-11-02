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
  const detectButton = $("detect-button");
  const statusEl = $("status");
  const errorEl = $("error");
  const summaryEl = $("summary");
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
    detectButton.disabled = value || !selectedFile;
    statusEl.textContent = message;
    statusEl.classList.toggle("loading", value);
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
    preview.onload = () => {
      overlay.width = preview.naturalWidth;
      overlay.height = preview.naturalHeight;
      viewerEl.hidden = false;
      fitToWidth();
    };
    preview.onerror = () => {
      selectedFile = null;
      viewerEl.hidden = true;
      detectButton.disabled = true;
      showError("The selected file could not be displayed as an image.");
    };
    preview.src = objectUrl;
    detectButton.disabled = false;
  }

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
  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));
  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragover");
    const files = event.dataTransfer.files;
    if (files.length > 1) {
      showError("Please drop a single image.");
      return;
    }
    selectFile(files[0]);
  });
  // Prevent the browser from navigating to a file dropped outside the drop zone.
  for (const type of ["dragover", "drop"]) {
    window.addEventListener(type, (event) => event.preventDefault());
  }

  detectButton.addEventListener("click", detect);
  $("zoom-in").addEventListener("click", () => applyZoom(zoom * ZOOM_STEP));
  $("zoom-out").addEventListener("click", () => applyZoom(zoom / ZOOM_STEP));
  $("zoom-fit").addEventListener("click", fitToWidth);
})();
