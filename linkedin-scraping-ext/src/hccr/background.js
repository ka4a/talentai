import { alertMessages, API } from './const';

function addProfileHandler(req, sender, sendResponse) {
  const profile = req.data;

  profile.from = 'ext';
  fetch(API.crawlProfile, {
    method: 'POST', // or 'PUT'
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profile),
  })
    .then((response) => {
      console.log('Profile data', profile);
      console.log('Server response', response);
      return response.json();
    })
    .then((data) => {
      console.log('Add profile Success:', data);
      sendResponse(data);
    })
    .catch((error) => {
      console.error('Add profile Error:', error);
      sendResponse({ result: 'FAIL', error: { message: alertMessages.apiError } });
    });
}

function checkExistsHandler(req, sender, sendResponse) {
  fetch(API.checkExists, {
    method: 'POST', // or 'PUT'
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ linkedin_url: req.url }),
  })
    .then((response) => response.json())
    .then((data) => {
      console.log('Check Exist Success:', data);
      sendResponse(data);
    })
    .catch((error) => {
      console.error('Check Exist Error:', error);
    });
}

const MESSAGE_HANDLERS = {
  checkExists: checkExistsHandler,
  addProfile: addProfileHandler,
};

chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  const handler = MESSAGE_HANDLERS[req.cmd];

  if (handler) {
    handler(req, sender, sendResponse);
    return true;
  }
});
