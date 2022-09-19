import React, { memo, useEffect, useCallback } from 'react';
import { Prompt, useLocation } from 'react-router-dom';

import PropTypes from 'prop-types';

function BlockingPrompt({ when, message }) {
  const { hash } = useLocation();
  usePromptOnTabClose(message, when);

  const getMessage = useCallback(
    (nextLocation) => (nextLocation.hash !== hash ? true : message),
    [message, hash]
  );

  return <Prompt when={when} message={getMessage} />;
}

function usePromptOnTabClose(message, when) {
  useEffect(() => {
    const beforeUnloadHandler = (event) => {
      event.preventDefault();
      event.returnValue = ''; // required to activate prompt
      // not shown in some browsers
      return message;
    };

    if (when) window.addEventListener('beforeunload', beforeUnloadHandler);

    return () => {
      window.removeEventListener('beforeunload', beforeUnloadHandler);
    };
  }, [message, when]);
}

BlockingPrompt.propTypes = {
  when: PropTypes.bool.isRequired,
  message: PropTypes.string.isRequired,
};

export default memo(BlockingPrompt);
