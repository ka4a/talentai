import $ from 'jquery';
import _ from 'lodash';

import getProposalPresetTitleStr from '../common/utils/getProposalPresetTitleStr';

import {
  alertMessages,
  API,
  btnText,
  getCandidatePageURL,
  getCsrfToken,
  websiteBaseUrl,
} from './const';

function handleAjaxError(xhr, sendResponse) {
  let error = alertMessages.requestError;
  let resp = {};

  try {
    resp = JSON.parse(xhr.responseText);
  } catch (e) {}

  if (_.has(resp, 'detail')) {
    error = resp.detail;
  } else if (process.env.NODE_ENV === 'development') {
    error = `Error ${xhr.status}`;
  }

  sendResponse({ error });
}

const waitingTabLoaded = {};

function waitTabLoaded(tabId) {
  return new Promise((resolve) => {
    waitingTabLoaded[tabId] = resolve;
  });
}

chrome.tabs.onUpdated.addListener(function (tabId, changeInfo, tab) {
  if (changeInfo.status === 'complete') {
    const tabLoadedResolve = waitingTabLoaded[tabId];

    if (tabLoadedResolve) {
      waitingTabLoaded[tabId] = undefined;
      tabLoadedResolve();
    }
  }
});

function createTabPromise(createProperties) {
  return new Promise((resolve) => {
    chrome.tabs.create(createProperties, resolve);
  });
}

function naiveSendTabMessagePromise(tab, message) {
  return new Promise((resolve) => {
    chrome.tabs.sendMessage(tab.id, message, resolve);
  });
}

async function openAndScrapeHandler(req, sender, sendResponse) {
  const tab = await createTabPromise({ url: req.url + '?from=ext' });
  await waitTabLoaded(tab.id);
  const response = await naiveSendTabMessagePromise(tab, {
    cmd: req.retrieveData ? 'scrapeData' : 'scrape',
  });
  chrome.tabs.remove(tab.id);

  if (sender.tab) {
    chrome.tabs.update(sender.tab.id, { active: true });
  }

  sendResponse(response);
}

function addProfileHandler(req, sender, sendResponse) {
  getCsrfToken().then((csrfToken) => {
    $.ajax({
      type: 'POST',
      url: API.crawlProfile,
      dataType: 'json',
      data: JSON.stringify(req.data),
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json',
      },
      success: function (data) {
        sendResponse(data);
      },
      error: function (xhr, status, e) {
        handleAjaxError(xhr, sendResponse);
      },
    });
  });
}

function checkExistsHandler(req, sender, sendResponse) {
  checkCandidateExists(req.url).then(
    (data) => {
      sendResponse(data);
    },
    (xhr, status, e) => {
      handleAjaxError(xhr, sendResponse);
    }
  );
}

function checkCandidateExists(profileURL) {
  return new Promise((resolve, reject) => {
    getCsrfToken().then((csrfToken) => {
      $.ajax({
        type: 'POST',
        url: API.checkExists,
        dataType: 'json',
        data: JSON.stringify({ linkedinUrl: profileURL }),
        headers: {
          'X-CSRFToken': csrfToken,
          'Content-Type': 'application/json',
        },
      })
        .then(resolve)
        .catch(reject);
    });
  });
}

function openCandidatePageHandler(req, sender, sendResponse) {
  const url = getCandidatePageURL(req.candidateId);

  chrome.tabs.create({ url }, function (tab) {
    if (req.dataId) {
      waitTabLoaded(tab.id).then(function () {
        chrome.tabs.sendMessage(tab.id, {
          cmd: 'openDataMerge',
          dataId: req.dataId,
        });
      });
    }
  });
}

const store = {
  proposalPreset: null,
  jobs: [],
  title: null,
  selectionTitle: btnText.candidatesDB,
};

const storeOnChange = {
  proposalPreset: 'defined below',
};

function setStoreField(field, payload) {
  if (store[field] !== payload) {
    if (storeOnChange[field]) {
      storeOnChange[field](payload, store[field]);
    }
    store[field] = payload;

    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {
        cmd: 'bgFieldWasChanged',
        field,
        payload,
      });
    });
  }
}

const STAGE_TITLE = {
  longlist: 'Longlist',
  shortlist: 'ShortList',
};

function getStoreSelectedTitle(val) {
  if (!val) {
    return btnText.candidatesDB;
  }
  const { job: jobId, stage } = JSON.parse(val);

  const job = store.jobs.find((e) => e.id === jobId);

  const stageTitle = STAGE_TITLE[stage];

  if (!(job && stageTitle)) {
    return btnText.candidatesDB;
  }
  return getProposalPresetTitleStr(job, stageTitle);
}

storeOnChange.proposalPreset = function (val) {
  setStoreField('selectionTitle', getStoreSelectedTitle(val));
};

function setBgFieldHandler(req, sender, sendResponse) {
  setStoreField(req.field, req.payload);
  if (sendResponse) sendResponse(store[req.field]);
}

function getBgFieldHandler(req, sender, sendResponse) {
  sendResponse(store[req.field]);
}

function fetchJobOptionsHandler(req, sender, sendResponse) {
  const title = _.get(req, 'payload.title', '');
  if (title === store.title) return;
  const params = title ? `?${$.param({ search: title })}` : '';

  $.ajax({
    type: 'GET',
    url: `${API.jobs}${params}`,
    dataType: 'json',

    headers: {
      'Content-Type': 'application/json',
    },
    success: (payload) => {
      setStoreField('jobs', payload.results);
      setStoreField('title', title);
    },
    error: () => {
      setStoreField('jobs', []);
      setStoreField('title', title);
    },
  });
}

const MESSAGE_HANDLERS = {
  checkExists: checkExistsHandler,
  addProfile: addProfileHandler,
  openCandidatePage: openCandidatePageHandler,
  openAndScrape: openAndScrapeHandler,
  setBgField: setBgFieldHandler,
  getBgField: getBgFieldHandler,
  fetchJobOptions: fetchJobOptionsHandler,
};

chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
  const handler = MESSAGE_HANDLERS[req.cmd];

  if (handler) {
    handler(req, sender, sendResponse);
    return true;
  }
});
