const manifest = chrome.runtime.getManifest();
const extensionInfo = {
  version: manifest.version,
  name: manifest.name,
};

export const linkedinUrlRe = /^https?:\/\/(\w+\.)?linkedin\.com\/in\/(.+)/i;

let apiBaseUrl = 'https://zookeep.com/api/ext_api/';
export let websiteBaseUrl = 'https://zookeep.com/';

if (process.env.NODE_ENV === 'development') {
  apiBaseUrl = 'http://localhost:3000/api/ext_api/';
  websiteBaseUrl = 'http://localhost:3000/';
}

export function getCsrfToken() {
  return new Promise((resolve, reject) => {
    chrome.cookies.get({ url: websiteBaseUrl, name: 'csrftoken' }, function (cookie) {
      resolve(cookie ? cookie.value : null);
    });
  });
}

export const API = {
  checkExists: apiBaseUrl + 'check_linkedin_candidate_exists/',
  crawlProfile: apiBaseUrl + 'add_linkedin_candidate/',
  jobs: apiBaseUrl + 'job_search/',
};

export function getCandidatePageURL(candidateId) {
  return websiteBaseUrl + 'candidate/' + candidateId + '/edit';
}

export const btnText = {
  exists: 'View on ZooKeep.io',
  add: 'Add to ZooKeep.io',
  existsInSL: 'View', // search list, the button will be too long
  adding: 'Adding...',
  addInSL: 'View', // search list, the button will be too long
  scrapeInSL: 'Scrape',
  scrapeInProfile: 'Scrape',
  scraping: 'scraping',
  recrawl: 'ReCrawl',
  candidatesDB: 'Candidates DB',
};

export const btnID = {
  exists: 'zookeep__button_exists',
  add: 'zookeep__button_add',
  scrape: 'scrape',
  recrawl: 'zookeep__button_recrawl',
};

export const alertMessages = {
  extensionContextInvalidated:
    'Extension have been updated. Please refresh the page to continue',
  requestError: `${extensionInfo.name}. We got an error connecting to the server, please try again later or contact us`,
  defaultError:
    'An error occurred, please make sure you are logged into ZooKeep.io and/or try again later',
  crawlDone: "We've added this profile successfully",
  getInfoError:
    'We could not get the profile info, please try again later or contact us',
};
