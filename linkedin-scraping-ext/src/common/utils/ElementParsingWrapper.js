import getDateRangeData from './getDateRangeData';
import getText from './getText';
import getVisibleText from './getVisibleText';

export default class ElementParsingWrapper {
  constructor(element) {
    this.element = element;
  }
  find(selector) {
    return this.element.find(selector);
  }
  get(selector, index = null) {
    let container = this.find(selector);
    if (index !== null) {
      container = container.eq(index);
    }
    return getText(container);
  }
  getVisible(selector) {
    return getVisibleText(this.find(selector));
  }
  getFirstOf(selectorList, index) {
    for (let selector of selectorList) {
      const text = this.get(selector, index);
      if (text) return text;
    }
    return '';
  }
  getDateRange(selector, index, lang) {
    return getDateRangeData(this.get(selector, index), lang);
  }
}
