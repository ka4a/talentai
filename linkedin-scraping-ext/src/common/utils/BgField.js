import sendMessagePromise from './sendMessagePromise';

export default class BgField {
  constructor(fieldName) {
    this.name = fieldName;
    this._unwatchList = [];
  }
  get() {
    return sendMessagePromise({
      cmd: 'getBgField',
      field: this.name,
    });
  }
  set(payload) {
    chrome.runtime.sendMessage({
      cmd: 'setBgField',
      field: this.name,
      payload,
    });
  }

  getAndWatch(callback) {
    this.get().then(callback);
    return this.watch(callback);
  }

  watch(callback) {
    const handler = (msg, sender, sendResponse) => {
      if (msg.cmd === 'bgFieldWasChanged' && msg.field === this.name) {
        callback(msg.payload, sender, sendResponse);
      }
    };

    chrome.runtime.onMessage.addListener(handler);

    const unwatch = () => {
      chrome.runtime.onMessage.removeListener(handler);
      this._unwatchList.splice(this._unwatchList.indexOf(unwatch), 1);
    };

    this._unwatchList.push(unwatch);

    return unwatch;
  }

  unwatchAll() {
    this._unwatchList.forEach((f) => f());
  }
}
