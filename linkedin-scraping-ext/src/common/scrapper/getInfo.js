import _ from 'lodash';
import $ from 'jquery';

import getMultiLineText from '../utils/getMultiLineText';
import getSingleLineText from '../utils/getSingleLineText';
import getText from '../utils/getText';
import ElementParsingWrapper from '../utils/ElementParsingWrapper';
import getListItemAttr from '../utils/getListItemAttr';
import getExperienceList from './getExperienceList';
import loadFileAsDataURL from './loadFileAsDataURL';

export default async function getInfo() {
  const lang = document.documentElement.getAttribute('lang');

  const userInfoEl = new ElementParsingWrapper($('.pv-text-details__left-panel'));

  const userInfo = {
    name: userInfoEl.get('div:first > h1'),
    headline: userInfoEl.get('.text-body-medium'),
    city: userInfoEl.get('div:last > span:first'),
    company: getSingleLineText(
      document.querySelector('[aria-label="Current company"]') ||
        document.querySelector('.pv-top-card--experience-list-item')
    ),
    summary:
      getText($('.pv-about-section > div:last')) ||
      getMultiLineText(
        document.querySelector('.pv-about__summary-text .lt-line-clamp__raw-line')
      ) ||
      getText($('.pv-top-card-section__summary-text .lt-line-clamp__line')),
    contactInfo: {
      website: getListItemAttr('section.ci-websites', 'li a', 'href'),
      twitter: getListItemAttr('section.ci-twitter', 'li a', 'href'),
      phone: getListItemAttr(
        'section.ci-phone',
        '.pv-contact-info__ci-container',
        (e) =>
          e
            .text()
            .replace(/\([^+0-9]+\)/, '')
            .trim()
      ),
      linkedIn: window.location.href
        .replace('detail/contact-info/', '')
        .replace('?from=ext', ''),
    },
    education: getListItemAttr('.education-section', 'li', (element) => {
      let el = new ElementParsingWrapper(element);
      return {
        school: el.get('h3'),
        degree: el.getVisible('.pv-entity__degree-name'),
        fos: el.getVisible('.pv-entity__fos'),
        desc: getMultiLineText(el.find('.pv-entity__extra-details')[0]),
        ...el.getDateRange('.pv-entity__dates span', 1, lang),
      };
    }),
    experience: getExperienceList(),
  };

  const emailEl = new ElementParsingWrapper($('section.ci-email'));
  const email = emailEl.get('.pv-contact-info__contact-link');
  if (email) userInfo.contactInfo.email = email;

  if (!userInfo.company && userInfo.experience.length) {
    userInfo.company = userInfo.experience[0].org;
  }

  userInfo.skills = [];
  $('.pv-skill-category-entity__name-text').map((x, e) => {
    userInfo.skills.push(getText($(e)));
  });

  const photoUrl = $('.pv-top-card__photo').attr('src');

  const validPhotoUrl =
    photoUrl &&
    !_.includes(photoUrl, 'static.licdn.com/') &&
    !_.includes(photoUrl, 'data:image/gif');

  if (validPhotoUrl) {
    userInfo.photo = { url: photoUrl };
    userInfo.photoBase64 = await loadFileAsDataURL(photoUrl);
  }

  return userInfo;
}
