import React, { memo } from 'react';
import { useSelector } from 'react-redux';
import { ToastContainer } from 'react-toastify';

import { Alert, ErrorWindow, CookieUsagePopup, DataMergeListener } from '@components';

const Popups = () => {
  const cookieUsage = useSelector((state) => state.settings.cookieUsage);
  const isLoaded = useSelector((state) => state.user.isLoaded);

  return (
    <>
      <Alert />

      <DataMergeListener />

      {!cookieUsage && isLoaded && <CookieUsagePopup />}

      <ErrorWindow />

      <ToastContainer
        position='top-right'
        autoClose={5000}
        hideProgressBar
        newestOnTop={false}
        closeOnClick={false}
        rtl={false}
        pauseOnVisibilityChange
        draggable={false}
        pauseOnHover
      />
    </>
  );
};

export default memo(Popups);
