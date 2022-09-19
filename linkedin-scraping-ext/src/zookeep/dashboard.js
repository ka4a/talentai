import { linkedinUrlRe } from './const';

var s = document.createElement('script');
s.setAttribute('type', 'text/javascript');
s.innerText = 'window.extInstalled = true;';
document.getElementsByTagName('body')[0].appendChild(s);

const isLinkedInUrl = (url) => url && url.match(linkedinUrlRe);

function oldOpenPageAndAddCandidateHandler(data) {
  if (!isLinkedInUrl(data.url)) return;

  chrome.runtime.sendMessage(
    {
      cmd: 'openAndScrape',
      url: data.url,
    },
    function (response) {
      const { dataId, merge } = response;

      if (dataId && merge) {
        window.postMessage({ type: 'TAB_OPEN_DATA_MERGE', dataId: dataId }, '*');
      }
    }
  );
}

function trySendMessagePromise(message) {
  return new Promise((resolve) => {
    try {
      chrome.runtime.sendMessage(message, resolve);
    } catch (error) {
      resolve({ error });
    }
  });
}

function rehydrateError(plainError) {
  const error = new Error(plainError.message);
  error.name = plainError.name;
  error.response = plainError.response;
  error.columnNumber = plainError.columnNumber;
  error.lineNumber = plainError.lineNumber;
  error.fileName = plainError.fileName;
  error.stack = plainError.stack;
}

async function openPageAndScrapeHandler(data) {
  if (!isLinkedInUrl(data.payload.url)) {
    window.postMessage({
      responseTo: data.id,
      error: new Error('Invalid profile URL'),
    });
    return;
  }

  const response = await trySendMessagePromise({
    cmd: 'openAndScrape',
    url: data.payload.url,
    retrieveData: this.retrieveData,
  });

  let { result, error, ...payload } = response || {};
  if (error && !(error instanceof Error)) {
    error = rehydrateError(error);
  }

  window.postMessage({
    responseTo: data.id,
    payload,
    error,
  });
}

const windowMessageHandlers = {
  EXT_OPEN_PAGE: oldOpenPageAndAddCandidateHandler,
  EXT_OPEN_PAGE_AND_ADD_CANDIDATE: openPageAndScrapeHandler,
  EXT_OPEN_PAGE_AND_RETRIEVE_DATA: openPageAndScrapeHandler.bind({
    retrieveData: true,
  }),
};

window.addEventListener('message', function (event) {
  if (event.source !== window) {
    return;
  }

  const handleMessage = windowMessageHandlers[event.data.type];
  if (handleMessage) {
    handleMessage(event.data);
  }
});

function openDataMergeHandler(req, sender, sendResponse) {
  window.postMessage({ type: 'TAB_OPEN_DATA_MERGE', dataId: req.dataId }, '*');
}

const MESSAGE_HANDLERS = {
  openDataMerge: openDataMergeHandler,
};

chrome.runtime.onMessage.addListener(function (req, sender, sendResponse) {
  const handler = MESSAGE_HANDLERS[req.cmd];

  if (handler) {
    handler(req, sender, sendResponse);
    return true;
  }
});
