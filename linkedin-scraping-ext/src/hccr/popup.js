// trigger content scripts' scraper, send message to background
import $ from 'jquery';
import { alertMessages } from './const';

let currentTab = 0;

$(function () {
  let viewOnZohoBtn = document.getElementById('viewOnZoho');
  let addToZohoBtn = document.getElementById('addToZoho');
  let recrawlProfileBtn = document.getElementById('recrawlSingle');

  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    currentTab = tabs[0];

    // Interface navigation
    getCurrentCookies().then((cookie) => {
      if (cookie) {
        decideStartView();
      } else {
        showSection('#login');
        switchToHCCRTab();
      }
    });
  });

  function decideStartView() {
    if (isProfilePageUrl(currentTab.url)) {
      showSection('#loading');
      chrome.runtime.sendMessage(
        { cmd: 'checkExists', url: currentTab.url },
        (resp) => {
          console.log(resp);
          if (resp.exists) {
            // view, refresh buttons
            viewOnZohoBtn.dataset.candidateId = resp.candidateId;
            showSection('#single_exists');
          } else {
            // add to zoho button
            showSection('#single');
          }
        }
      );
    } else {
      showSection('#page_not_supported');
    }
  }

  // button listeners
  viewOnZohoBtn.addEventListener('click', () => {
    const candidateId = viewOnZohoBtn.getAttribute('data-candidate-id');
    if (candidateId) {
      chrome.tabs.create({
        url: `https://tool.hccr.com/candidates/${candidateId}/zoho`,
      });
    } else {
      decideStartView();
    }
  });

  [addToZohoBtn, recrawlProfileBtn].forEach((btn) => {
    btn.addEventListener('click', () => {
      showSection('#loading');
      chrome.tabs.sendMessage(currentTab.id, { cmd: 'scrape' }, function (response) {
        console.log('Scrape response', response);

        $('#recrawlSingle').hide();
        if (response.result === 'OK') {
          showAlert('success');
        } else {
          showAlert('danger', response.error.message || alertMessages.defaultError);
        }
        decideStartView();
      });
    });
  });
});

function showSection(id) {
  $('section').hide();
  $(id).fadeIn('fast');
}

function showAlert(level, message) {
  let alertElem = $('#alertElement');
  alertElem.addClass(`alert-${level}`);
  if (message) alertElem.text(message);
  alertElem.show();
}

function getCurrentCookies() {
  return chrome.cookies.get({
    url: 'https://tool.hccr.com',
    name: 'remember_token',
  });
}

function switchToHCCRTab() {
  chrome.tabs.query({}, (tabs) => {
    let opened = false;
    let openId = -1;
    tabs.forEach((tab) => {
      if (tab.url.includes('tool.hccr.com')) {
        opened = true;
        openId = tab.id;
      }
    });

    if (!opened) {
      chrome.tabs.create({ url: 'https://tool.hccr.com/' });
    } else {
      chrome.tabs.update(openId, { activate: true });
    }
  });
}

// Checks if url belongs to a linkedin profile
function isProfilePageUrl(url) {
  return url.indexOf('//www.linkedin.com/in') > -1;
}
