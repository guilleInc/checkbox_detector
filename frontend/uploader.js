const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const ALLOWED_TYPES = ["image/png", "image/jpeg"];
const ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg"];

function isSupported(file) {
  const name = file.name.toLowerCase();
  return ALLOWED_TYPES.includes(file.type)
    || (!file.type && ALLOWED_EXTENSIONS.some((extension) => name.endsWith(extension)));
}

// Drag-and-drop / file-picker area. Calls onFiles with the valid files only.
export function createUploader({ onFiles }) {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const errorEl = document.getElementById("upload-error");

  function showError(message) {
    errorEl.textContent = message;
    errorEl.hidden = !message;
  }

  function handle(fileList) {
    const valid = [];
    const problems = [];
    for (const file of Array.from(fileList)) {
      if (!isSupported(file)) {
        problems.push(`${file.name}: unsupported file type (use PNG, JPG or JPEG).`);
      } else if (file.size > MAX_UPLOAD_BYTES) {
        problems.push(`${file.name}: larger than the 10 MiB limit.`);
      } else {
        valid.push(file);
      }
    }
    showError(problems.join(" "));
    if (valid.length) onFiles(valid);
  }

  fileInput.addEventListener("change", () => {
    handle(fileInput.files);
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
    handle(event.dataTransfer.files);
  });
  // Prevent the browser from navigating to a file dropped outside the drop zone.
  for (const type of ["dragover", "drop"]) {
    window.addEventListener(type, (event) => event.preventDefault());
  }

  return { showError };
}
