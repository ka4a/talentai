export default function getVisibleText(findResult) {
  const textContent = [];
  findResult.map(function (i, e) {
    for (let node of e.childNodes) {
      if (node.className !== 'visually-hidden' && node.textContent) {
        const content = node.textContent.trim();
        if (content) textContent.push(content);
      }
    }
  });
  return textContent.join(' ');
}
