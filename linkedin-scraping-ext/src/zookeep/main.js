import $ from 'jquery';

import { alertMessages, btnID, btnText, linkedinUrlRe } from './const.js';
import getInfo from '../common/scrapper/getInfo';
import FloatingPanel from './components/FloatingPanel';
import renderScrappingInProgressScreen from './components/renderScrappingInProgressScreen';
import sendMessagePromise from '../common/utils/sendMessagePromise';
import handleMessageAsync from '../common/utils/handleMessageAsync';
import withCandidateOption from './utils/withCandidateOption';
import storeApi from './storeApi';
import repeatUntilResolve from '../common/utils/repeatUntilResolve';

function fetchJobs(title) {
  chrome.runtime.sendMessage({
    cmd: 'fetchJobOptions',
    payload: { title },
  });
}

let selectedOption = '';
storeApi.selectionTitle.getAndWatch((value) => {
  selectedOption = value;
  $('.insert-selected-candidate-option').each(function () {
    this.innerText = value;
  });
});

fetchJobs('');

function onPresetSelect(value) {
  storeApi.proposalPreset.set(value);
}

const floatingPanel = new FloatingPanel({
  onSelect: onPresetSelect,
  fetchOptions: fetchJobs,
});

floatingPanel.mount(document.body);

storeApi.jobs.getAndWatch((jobs) => {
  floatingPanel.jobMenu.options = withCandidateOption(jobs);
  if (!floatingPanel.visible) floatingPanel.visible = true;
});

storeApi.proposalPreset.getAndWatch((value) => {
  floatingPanel.getPreset(value);
});

storeApi.title.watch((title) => {
  floatingPanel.jobMenu.filter = title;
});

chrome.runtime.onMessage.addListener(function (req, sender, sendResponse) {
  switch (req.cmd) {
    case 'scrape':
      return handleMessageAsync(scrapeProfile(), sendResponse);
    case 'scrapeData':
      return handleMessageAsync(scrapeProfileData(), sendResponse);
  }
});

let page = getCurrentPageType();

if (page === 'profile' && !window.location.href.includes('?from=ext')) {
  checkCandidateExists(window.location.href).then((resp) => {
    const btnArea = $('button.pv-s-profile-actions__overflow-toggle')
      .closest('div')
      .parent();
    injectBtn(btnArea, resp);
  });
}

function injectButtonToSearchList(wrapper, actions) {
  let profileSel = wrapper.find('a.search-result__result-link');

  if (profileSel.length > 1) {
    profileSel = profileSel.eq(0);
  }

  const profileURL = profileSel.prop('href');
  const goodUrl = profileURL && profileURL.match(linkedinUrlRe);

  if (!goodUrl) {
    return;
  }

  checkCandidateExists(profileURL).then((resp) => {
    let btnArea = actions || wrapper.find('.search-result__actions');

    if (btnArea.length > 1) {
      // some people showing send InMail button inject before that button.
      btnArea = btnArea.eq(1);
    }

    injectBtn(btnArea, resp, true);
  });
}

// Navigation detection observer
const observer = new MutationObserver(function (mutations) {
  for (let mutation of mutations) {
    // Navigated to a profile from some other type of page (profile el is added)
    let isProfile =
      mutation.type === 'childList' &&
      Array.from(mutation.addedNodes).some((el) => el.id === 'profile-wrapper');

    // Navigated to a profile from another profile ("Contact info" link is updated)
    let isAnotherProfile =
      mutation.type === 'attributes' &&
      mutation.attributeName === 'href' &&
      'data-control-name' in mutation.target.attributes &&
      mutation.target.attributes['data-control-name'].value === 'contact_see_more';

    if (isProfile || isAnotherProfile) {
      console.log('NAVIGATED TO A PROFILE', isProfile, isAnotherProfile);

      // TODO: move to fn, repeated:
      checkCandidateExists(window.location.href).then((resp) => {
        const btnArea = $('button.pv-s-profile-actions__overflow-toggle')
          .closest('div')
          .parent();
        injectBtn(btnArea, resp);
      });
    }

    const isActionPanelAddedToSearchResult =
      mutation.type === 'childList' &&
      mutation.target.className === 'search-result__wrapper' &&
      mutation.addedNodes.length > 0;
    if (isActionPanelAddedToSearchResult) {
      mutation.addedNodes.forEach((node) => {
        if (node.className === 'search-result__actions') {
          injectButtonToSearchList($(mutation.target), $(node));
        }
      });
    }
  }
});

//wait for the target dom

repeatUntilResolve((resolve) => {
  const anchor = document.getElementsByClassName('authentication-outlet');
  if (anchor.length > 0) resolve(anchor[0]);
}, 10).then((anchor) => {
  observer.observe(anchor, {
    subtree: true,
    attributes: true,
    attributeOldValue: true,
    childList: true,
  });
  $(anchor)
    .find('.search-result__actions') // we need to make sure the place we inject the button exists
    .parent('.search-result__wrapper')
    .each(function () {
      injectButtonToSearchList($(this));
    });
});

//events listener

$('body')
  .on('click', `.${btnID.exists}`, function () {
    openCandidatePage($(this).attr('data-candidateID'));
  })
  .on('click', `.${btnID.add}`, onScrapeProfile)
  .on('click', `.${btnID.recrawl}`, onScrapeProfile);

async function onScrapeProfile() {
  const $btn = $(this);
  const profileURL = $btn.attr('data-profileurl');

  const previousChildren = $btn.children();
  const restoreBtn = () => {
    $btn.empty();
    $btn.append(previousChildren);
    $btn.prop('disabled', false);
  };

  $btn.text(btnText.adding).prop('disabled', true);
  let data = {};

  try {
    const userInfo = await sendMessagePromise({
      cmd: 'openAndScrape',
      url: profileURL,
      retrieveData: true,
    });

    data = await sendMessagePromise({ cmd: 'addProfile', data: userInfo });
  } catch (e) {
    if (e && e.message && e.message.indexOf('context invalidated') > 0) {
      alert(alertMessages.extensionContextInvalidated);
      return;
    }
    alert(e);
    restoreBtn();
    return;
  }

  if (data.result && data.result.toLowerCase() === 'ok') {
    if (data.merge) {
      openCandidatePage(data.candidateId, data.dataId);
    }

    if (!$btn.hasClass('zookeep__button_recrawl')) {
      $btn
        .removeClass('zookeep__button_add')
        .addClass('zookeep__button_exists')
        .text(btnText.exists)
        .attr('data-candidateID', data.candidateId);
    } else {
      restoreBtn();
    }
  } else {
    if (data.error) {
      alert(data.error);
    } else {
      alert(alertMessages.defaultError);
    }

    restoreBtn();
  }

  $btn.prop('disabled', false);
}

function scrollToBottom() {
  return new Promise((resolve) => {
    const scrollToElements = [
      ...Array.from($('.pv-deferred-area:last')),
      ...Array.from($('.pv-deferred-area--pending')),
    ];
    console.log('Neet to scroll to els: ', scrollToElements);

    const c = setInterval(function () {
      if (scrollToElements.length === 0) {
        clearInterval(c);
        resolve(true);
        return;
      }

      const el = $(scrollToElements.pop());
      console.log('scrolling to', el);

      $([document.documentElement, document.body]).animate(
        {
          scrollTop: el.offset().top,
        },
        100
      );
    }, 500);
  });
}

function sleep(timeout) {
  return new Promise((resolve) => {
    setTimeout(function () {
      resolve(true);
    }, timeout);
  });
}

function clickAll(selector) {
  // fixes clicking on `a` tags
  selector.each((x, e) => e.click());
}

function clickMoreButtons(waitingTime) {
  return new Promise((resolve, reject) => {
    const selectors = [
      'button.pv-profile-section__card-action-bar',
      '.pv-profile-section__see-more-inline',
      '.lt-line-clamp__more',
      'a[data-control-name="contact_see_more"]',
    ]
      .map((str) => $(str))
      .filter((selector) => selector.length > 0);

    if (selectors.length < 1) {
      reject(new Error('No buttons found'));
    }

    selectors.forEach(clickAll);

    window.scrollTo(0, 0);

    let untilOpen = null;
    let rejectionTimeout = null;
    if (waitingTime) {
      setTimeout(function () {
        reject(new Error("Coudn't open spoilers"));
        clearInterval(untilOpen);
      }, waitingTime);
    }

    untilOpen = setInterval(() => {
      if ($('div.pv-profile-section__actions-inline--loading').length > 0) {
        return;
      }

      if ($('.pv-contact-info__contact-type').length === 0) {
        // contact info modal
        return;
      }

      clearTimeout(rejectionTimeout);
      clearInterval(untilOpen);
      resolve(true);
    }, 100);
  });
}

async function scrapeProfileData() {
  $(document.body).append(renderScrappingInProgressScreen());

  try {
    console.log('scrolling to bottom');
    await scrollToBottom();
    console.log('sleeping');
    await sleep(3000);
    console.log('clicking more buttons');

    await clickMoreButtons();
    console.log('buttons clicked');
  } catch (error) {
    throw Error("Couldn't read the page.");
  }

  console.log('getting info');
  let userInfo = null;

  try {
    userInfo = await getInfo();
  } catch (e) {
    alert(alertMessages.getInfoError);
    throw e;
  }

  const proposalPreset = await storeApi.proposalPreset.get();
  userInfo.proposal = proposalPreset ? JSON.parse(proposalPreset) : null;

  userInfo.extVersion = chrome.runtime.getManifest().version;

  $('.artdeco-modal__dismiss').click(); // contact info modal

  window.scrollTo(0, 0);

  $('#ext-block-screen').remove();

  return userInfo;
}

async function scrapeProfile() {
  const userInfo = await scrapeProfileData();
  return await sendMessagePromise({ cmd: 'addProfile', data: userInfo });
}

//add button to the page
function injectBtn(btnArea, resp, isSearchList) {
  let oldAddBtn = btnArea.find('.zookeep__button'),
    oldReCrawlBtn = btnArea.find('.zookeep__button_recrawl');
  if (oldAddBtn.length > 0) {
    let oldProfileUrl = oldAddBtn.attr('data-profileurl');
    if (oldProfileUrl === resp.profileURL) {
      return;
    }
  }
  oldAddBtn.remove();
  oldReCrawlBtn.remove();

  if (resp) {
    let error = resp.error ? ` (${resp.error})` : '';

    const getButtonHtml = (className, title, error = '', isExistButton) => `
      <button
        class='zookeep__button zookeep__button_withSubtitle ${className}'
        data-candidateID='${resp.candidateId}'
        data-profileurl='${resp.profileURL}'
        ${resp.error ? 'disabled' : ''}
      >
        <div>${title}${error}</div>
        ${
          isExistButton
            ? ''
            : `<div class="zookeep__button__subtitle insert-selected-candidate-option">
              ${selectedOption}
          </div>`
        }
      </button>
    `;

    if (resp.candidateId) {
      btnArea.prepend(
        getButtonHtml('zookeep__button_exists', btnText.exists, error, true)
      );

      if (!isSearchList) {
        $('.zookeep__button').after(
          getButtonHtml('zookeep__button_recrawl', 'Refresh data', error, true)
        );
      }
    } else {
      btnArea.prepend(getButtonHtml('zookeep__button_add', btnText.add, error));
    }
  }
}

function openCandidatePage(candidateId, dataId) {
  chrome.runtime.sendMessage({
    cmd: 'openCandidatePage',
    candidateId,
    dataId,
  });
}

function getCurrentPageType() {
  const url = window.location.href;

  if (url.includes('.com/in/')) {
    return 'profile';
  } else if (url.includes('/search/results/')) {
    return 'searchList';
  }
}

function checkCandidateExists(url) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ cmd: 'checkExists', url: url }, function (resp) {
      resp.profileURL = url;
      resolve(resp);
    });
  });
}
