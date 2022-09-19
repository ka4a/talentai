import $ from 'jquery';

import ElementParsingWrapper from '../utils/ElementParsingWrapper';
import getMultiLineText from '../utils/getMultiLineText';

function parseExperienceElement(elem, lang, org) {
  const el = new ElementParsingWrapper($(elem));
  const descEl = el.find('.pv-entity__description');

  return {
    title: el.getVisible('h3'),
    org:
      org ||
      el.getFirstOf(
        ['.pv-position-entity__secondary-title', '.pv-entity__secondary-title'],
        0
      ),
    duration: el.get('.pv-entity__bullet-item-v2'),
    location: el.get('.pv-entity__location span', 1),
    desc: getMultiLineText(
      descEl.find('.lt-line-clamp__less').length
        ? descEl.find('.lt-line-clamp__raw-line:first-child')[0]
        : descEl[0]
    ),
    ...el.getDateRange('.pv-entity__date-range span', 1, lang),
  };
}

export default function getExperienceList() {
  const lang = document.documentElement.getAttribute('lang');

  const listElem = $('.experience-section');
  const result = [];
  if (listElem.length < 1) return;

  listElem.find('.pv-position-entity').map((i, expElem) => {
    const el = new ElementParsingWrapper($(expElem));

    // Case then experiences are grouped by company
    const orgExpListElem = el.find('ul.pv-entity__position-group');
    if (orgExpListElem.length > 0) {
      const org = el.getVisible('.pv-entity__company-summary-info>h3');

      orgExpListElem.find('li').map((i, expElemListItem) => {
        result.push(parseExperienceElement(expElemListItem, lang, org));
      });

      return;
    }

    result.push(parseExperienceElement(expElem, lang));
  });

  return result;
}
