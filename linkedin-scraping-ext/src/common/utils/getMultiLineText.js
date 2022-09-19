export default function getMultiLineText(el) {
  if (!el) {
    return '';
  }

  const text = el.innerText || el.textContent;
  return text.trim();
}
