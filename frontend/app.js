import { createGallery } from "./gallery.js";
import { createUploader } from "./uploader.js";
import { createViewer } from "./viewer.js";

// Each item: { file, url, status: "pending" | "detecting" | "done" | "error", boxes, error }
const items = [];
let activeIndex = -1;

const uploader = createUploader({ onFiles: addFiles });
const gallery = createGallery({
  onSelect(index) {
    activeIndex = index;
    render();
  },
  onRemove: removeItem,
});
const viewer = createViewer({ onDetect: detect, onImageError });

function render() {
  gallery.render(items, activeIndex);
  viewer.render(items[activeIndex] || null);
}

function addFiles(allFiles) {
  // Sample images already in the list are not added again.
  const files = allFiles.filter((file) => !(file.isSample
    && items.some((item) => item.file.isSample && item.file.name === file.name)));
  if (!files.length) return;
  activeIndex = items.length;
  items.push(...files.map((file) => ({
    file,
    url: URL.createObjectURL(file),
    status: "pending",
    boxes: null,
    error: "",
  })));
  render();
}

function removeItem(index) {
  URL.revokeObjectURL(items[index].url);
  items.splice(index, 1);
  if (index < activeIndex) activeIndex -= 1;
  else if (index === activeIndex) activeIndex = Math.min(index, items.length - 1);
  render();
}

function onImageError(item) {
  const index = items.indexOf(item);
  if (index === -1) return;
  removeItem(index);
  uploader.showError(`${item.file.name} could not be displayed as an image.`);
}

async function errorMessage(response) {
  try {
    const body = await response.json();
    if (typeof body.detail === "string") return body.detail;
  } catch (_) { /* fall through to the generic message */ }
  return `Detection failed (HTTP ${response.status}).`;
}

async function detect(item) {
  if (item.status === "detecting") return;
  item.status = "detecting";
  item.boxes = null;
  item.error = "";
  render();
  try {
    const body = new FormData();
    body.append("file", item.file);
    const response = await fetch("/detect", { method: "POST", body });
    if (response.ok) {
      const result = await response.json();
      item.boxes = Array.isArray(result.boxes) ? result.boxes : [];
      item.status = "done";
    } else {
      item.status = "error";
      item.error = await errorMessage(response);
    }
  } catch (_) {
    item.status = "error";
    item.error = "Could not reach the detection service. Please try again.";
  }
  render();
}

render();
