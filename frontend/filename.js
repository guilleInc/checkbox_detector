// Shortens a long file name to "start….ext", always keeping the extension visible.
export function truncateName(name, maxLength) {
  if (name.length <= maxLength) return name;
  const dot = name.lastIndexOf(".");
  const extension = dot > 0 && name.length - dot <= 6 ? name.slice(dot) : "";
  const keep = Math.max(1, maxLength - 1 - extension.length);
  return `${name.slice(0, keep)}…${extension}`;
}
