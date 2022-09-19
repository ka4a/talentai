// scraper here

import $ from 'jquery';

import { alertMessages } from './const.js';
import getInfo from '../common/scrapper/getInfo';
import sendMessagePromise from '../common/utils/sendMessagePromise';
import handleMessageAsync from '../common/utils/handleMessageAsync';

chrome.runtime.onMessage.addListener(function (req, sender, sendResponse) {
  switch (req.cmd) {
    case 'scrape':
      return handleMessageAsync(scrapeProfile(), sendResponse);
    case 'scrapeData':
      return handleMessageAsync(scrapeProfileData(), sendResponse);
  }
});

function scrollToBottom() {
  return new Promise((resolve) => {
    const scrollToElements = [
      ...Array.from($('.pv-deferred-area:last')),
      ...Array.from($('.pv-deferred-area--pending')),
    ];
    console.log('Neet to scroll to els: ', scrollToElements);

    const intervalId = setInterval(function () {
      if (scrollToElements.length === 0) {
        clearInterval(intervalId);
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
      console.log("No buttons found")
      resolve(true)
    }

    selectors.forEach(clickAll);

    window.scrollTo(0, 0);

    let untilOpen = null;
    if (waitingTime) {
      setTimeout(function () {
        reject(new Error("Coudn't open spoilers"));
        clearInterval(untilOpen);
      }, waitingTime);
    }

    resolve(true);
  });
}

async function scrapeProfileData() {
  try {
    console.log('scrolling to bottom');
    await scrollToBottom();
    console.log('sleeping');
    await sleep(3000);
    console.log('clicking more buttons');

    await clickMoreButtons();
    console.log('buttons clicked');
  } catch (error) {
    throw Error("Couldn't read the page. Try reloading the page.");
  }

  console.log('getting info');
  let userInfo = null;

  try {
    userInfo = await getInfo();
  } catch (e) {
    alert(alertMessages.getInfoError);
    throw e;
  }

  userInfo.extVersion = chrome.runtime.getManifest().version;

  $('.artdeco-modal__dismiss').click(); // contact info modal

  window.scrollTo(0, 0);

  $('#ext-block-screen').remove();

  return userInfo;
}

function transformEducationExperienceEntries(entries, allowed) {
  const transformedEntries = entries.map((entry) => {
    let date = entry.dateStart + ' - ';
    date += entry.currentlyPursuing ? 'Present' : entry.dateEnd;
    const parsedEntry = Object.fromEntries(
      Object.entries(entry).filter(([key, value]) => allowed.includes(key))
    );
    parsedEntry.date = date;
    return parsedEntry;
  });
  return transformedEntries;
}

function parseUserInfo(userInfo) {
  const userInfoKeys = [
    'name',
    'city',
    'company',
    'summary',
    'contactInfo',
    'education',
    'experience',
    'photo',
    'skills',
  ];
  const educationKeys = ['school', 'degree', 'fos', 'date'];
  const experienceKeys = ['title', 'org', 'date', 'location', 'duration', 'desc'];
  const parsedUserInfo = Object.fromEntries(
    Object.entries(userInfo).filter(([key, value]) => userInfoKeys.includes(key))
  );
  parsedUserInfo.education = transformEducationExperienceEntries(
    parsedUserInfo.education,
    educationKeys
  );
  parsedUserInfo.experience = transformEducationExperienceEntries(
    parsedUserInfo.experience,
    experienceKeys
  );

  return parsedUserInfo;
}

async function scrapeProfile() {
  const userInfo = await scrapeProfileData();
  return await sendMessagePromise({
    cmd: 'addProfile',
    data: parseUserInfo(userInfo),
  });
}
