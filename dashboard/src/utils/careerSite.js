import { CAREER_SITE_PATH } from '@constants';

export function getCareerSiteName(companyName) {
  if (!companyName) return '';
  return encodeURIComponent(companyName.replace(RE_SYMBOL, '').replace(RE_SPACE, '-'));
}

export function getCareerSiteUrl(careerSiteName = '') {
  return `${window.location.origin}${CAREER_SITE_PATH}/${careerSiteName}`;
}

const RE_SPACE = /\s/g;
const RE_SYMBOL = /[^\w\s]/g;
