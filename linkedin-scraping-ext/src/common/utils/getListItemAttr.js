import $ from 'jquery';

export default function getAttrList(listSelector, itemSelector, attr) {
  const listElem = $(listSelector);

  if (listElem.length < 1) return [];

  const result = [];
  const retriever = typeof attr === 'function' ? attr : (e) => e.attr(attr);

  listElem.find(itemSelector).map((i, e) => {
    const data = retriever($(e));
    if (data != null) {
      result.push(data);
    }
  });
  return result;
}
