export default function wrapInDiv(className, nodes) {
  const container = document.createElement('div');
  container.className = className;
  if (nodes.forEach) {
    nodes.forEach((node) => container.appendChild(node));
  } else {
    container.appendChild(nodes);
  }
  return container;
}
