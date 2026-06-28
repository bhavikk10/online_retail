export default function throttle(fn, wait = 0) {
  let last = 0;
  let timeout;
  let lastArgs;
  const run = () => {
    timeout = undefined;
    last = Date.now();
    fn(...(lastArgs || []));
    lastArgs = undefined;
  };
  const throttled = (...args) => {
    lastArgs = args;
    const now = Date.now();
    if (now - last >= wait) {
      clearTimeout(timeout);
      run();
    } else if (!timeout) {
      timeout = setTimeout(run, wait - (now - last));
    }
  };
  throttled.cancel = () => {
    clearTimeout(timeout);
    timeout = undefined;
    lastArgs = undefined;
  };
  throttled.flush = () => {
    if (timeout) {
      clearTimeout(timeout);
      run();
    }
  };
  return throttled;
}
