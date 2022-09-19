import toPlainError from './toPlainError';

export default function handleMessageAsync(promise, sendResponse) {
  promise.then(
    (response) => sendResponse(response),
    (error) =>
      sendResponse({
        result: 'FAIL',
        // make error plain to avoid losing data
        error: toPlainError(error),
      })
  );
  return true;
}
