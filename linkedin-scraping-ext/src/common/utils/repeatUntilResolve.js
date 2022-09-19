export default (condition, interval, attempts = null) =>
  new Promise((resolve, reject) => {
    let attemptsLeft = attempts;
    let intervalId = null;

    const stopAndResolve = (...args) => {
      clearInterval(intervalId);
      resolve(...args);
    };

    intervalId = setInterval(() => {
      if (attemptsLeft === null || attemptsLeft > 0) {
        condition(stopAndResolve);
        return;
      }
      if (attemptsLeft <= 0) {
        reject(Error(`Failed to meet conditions after ${attempts} attempts`));
        clearInterval(intervalId);
      }
    }, interval);
  });
