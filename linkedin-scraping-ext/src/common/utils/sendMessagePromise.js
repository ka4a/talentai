export default (data) =>
  new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(data, (response) => {
      if (response && response.error) {
        reject(response.error);
        return;
      }
      resolve(response);
    });
  });
