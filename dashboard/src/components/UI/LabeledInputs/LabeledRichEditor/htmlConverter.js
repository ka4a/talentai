import escapeHtml from 'escape-html';
import { Text } from 'slate';
import { jsx } from 'slate-hyperscript';

export const serialize = (node) => {
  if (Text.isText(node)) {
    let content = escapeHtml(node.text);
    if (node.bold) content = `<strong>${content}</strong>`;
    if (node.italic) content = `<em>${content}</em>`;
    if (node.underline) content = `<u>${content}</u>`;

    return content;
  }

  const children = node.children.map((n) => serialize(n)).join('');

  const types = {
    paragraph: `<p>${children}</p>`,
    'bulleted-list': `<ul>${children}</ul>`,
    'list-item': `<li>${children}</li>`,
  };

  return types[node.type] ?? children;
};

export const deserialize = (el) => {
  if (el.nodeType === 3) return el.textContent ?? '';
  else if (el.nodeType !== 1) return null;

  const children = Array.from(
    el.childNodes.length ? el.childNodes : [{ nodeType: 3, textContent: '' }]
  ).map(deserialize);

  switch (el.nodeName) {
    case 'BODY':
      return jsx('fragment', {}, children);
    case 'BR':
      return '\n';
    case 'P':
      return jsx('element', { type: 'paragraph' }, children);
    case 'UL':
      return jsx('element', { type: 'bulleted-list' }, children);
    case 'LI':
      return jsx('element', { type: 'list-item' }, children);
    case 'STRONG':
      return jsx('text', { bold: true }, children);
    case 'EM':
      return jsx('text', { italic: true }, children);
    case 'U':
      return jsx('text', { underline: true }, children);
    default:
      return el.textContent ?? '';
  }
};
