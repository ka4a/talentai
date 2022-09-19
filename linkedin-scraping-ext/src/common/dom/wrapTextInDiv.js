import wrapInDiv from './wrapInDiv';

export default function wrapTextInDiv(className, text) {
  return wrapInDiv(className, document.createTextNode(text));
}
