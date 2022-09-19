import $ from 'jquery';

export default function loadFileAsDataURL(url) {
  return new Promise((resolve, reject) => {
    $.ajax(url, {
      dataType: 'binary',
      xhr() {
        const myXhr = $.ajaxSettings.xhr();
        myXhr.responseType = 'blob';
        return myXhr;
      },
    }).then((response) => {
      const reader = new FileReader();

      reader.addEventListener(
        'load',
        () => {
          resolve(reader.result);
        },
        false
      );

      reader.addEventListener(
        'error',
        () => {
          reject(reader.error);
        },
        false
      );

      reader.readAsDataURL(response);
    });
  });
}
