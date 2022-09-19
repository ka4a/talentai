import { v4 as uuid } from 'uuid';

const postMessagePromise = (type, payload, timeout) => {
  const id = uuid();

  let abort = null;

  const promise = new Promise((resolve, reject) => {
    window.postMessage({ type, id, payload }, '*');

    let timeoutId = null;

    const catchResponse = (event) => {
      const { responseTo, error, payload } = event.data;
      if (responseTo === id) {
        clearTimeout(timeoutId);
        window.removeEventListener('message', catchResponse);
        if (error) reject(error);
        else resolve(payload);
      }
    };

    const cleanReject = (error) => {
      window.removeEventListener('message', catchResponse);
      reject(error);
    };

    abort = () => {
      cleanReject();
    };

    if (timeout) {
      timeoutId = setTimeout(() => {
        cleanReject(
          new Error(`Message response waiting limit (${timeout}ms) exceeded`)
        );
      });
    }

    window.addEventListener('message', catchResponse);
  });

  promise.abort = abort;

  return promise;
};

export const addLinkedInCandidate = (url, timeout) => {
  return postMessagePromise('EXT_OPEN_PAGE_AND_ADD_CANDIDATE', { url }, timeout);
};

export const retrieveLinkedInProfileData = (url, timeout) => {
  return postMessagePromise('EXT_OPEN_PAGE_AND_RETRIEVE_DATA', { url }, timeout);
};
