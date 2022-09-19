const manifest = chrome.runtime.getManifest();
const extensionInfo = {
  version: manifest.version,
  name: manifest.name,
};

export const linkedinUrlRe = /^https?:\/\/(\w+\.)?linkedin\.com\/in\/(.+)/i;

let apiBaseUrl = 'https://tool.hccr.com/api/';

export const API = {
  checkExists: apiBaseUrl + 'v2/candidate-exists',
  addUser: apiBaseUrl + 'add-user',
  userPageBaseURL: 'https://tool.hccr.com/candidates/', // + {candidateID} + "/zoho"
  crawlProfile: apiBaseUrl + 'v2/add-candidate',
};

export const alertMessages = {
  extensionContextInvalidated:
    'Extension have been updated. Please refresh the page to continue',
  requestError: `${extensionInfo.name}. We got an error connecting to the server, please try again later or contact us`,
  defaultError:
    'An error occurred, please make sure you are logged into tool.hccr.com and/or try again later',
  crawlDone: "We've added this profile successfully",
  getInfoError:
    'We could not get the profile info, please try again later or contact us',
  apiError: 'An API error occurred. Please try again later or contact us',
};
