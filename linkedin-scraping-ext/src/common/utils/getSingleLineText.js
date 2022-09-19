export default function getSingleLineText(el) {
  if (!el) {
    return '';
  }

  return el.textContent.trim();
}
