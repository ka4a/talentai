import React, { memo, useCallback, useState } from 'react';
import { Document, Page } from 'react-pdf';
import { useHistory } from 'react-router-dom';
import { useDispatch } from 'react-redux';

import { Trans } from '@lingui/macro';
import classnames from 'classnames';

import { client } from '@client';
import { fetchErrorHandler } from '@utils';
import { logoutUser, readUser } from '@actions';
import { useLegalAgreementsList, useLegalAgreementsFile } from '@swrAPI';
import { Button, Typography, WindowBackground, Loading } from '@components';

import styles from '../AuthPage.module.scss';

const Agreement = () => {
  const { privacyPolicyLink, termsAndConditionsLink } = useLegalAgreementsList();

  const history = useHistory();

  const dispatch = useDispatch();

  const { numPages, termsFile, onLoadSuccess } = usePreview();

  const onLogout = useCallback(() => {
    dispatch(logoutUser()).then(() => {
      history.push('/login');
    });
  }, [dispatch, history]);

  const onAgree = useCallback(async () => {
    try {
      await client.execute({
        operationId: 'user_update_legal',
        parameters: { data: { isLegalAgreed: true } },
      });
      await dispatch(readUser());

      history.push('/');
    } catch (error) {
      fetchErrorHandler(error);
    }
  }, [dispatch, history]);

  return (
    <WindowBackground
      className={classnames([styles.contentWrapper, styles.agreementWrapper])}
    >
      <Typography variant='h1' className={styles.contentHeader}>
        <Trans>Terms & Privacy Policy</Trans>
      </Typography>

      {termsFile && (
        <Document
          file={termsFile}
          className={styles.preview}
          onLoadSuccess={onLoadSuccess}
          loading={<Loading />}
        >
          {Array.from(new Array(numPages), (el, index) => (
            <Page key={`page_${index + 1}`} pageNumber={index + 1} loading='' />
          ))}
        </Document>
      )}

      <div className={styles.agreementFooter}>
        <a
          href={termsAndConditionsLink}
          target='_blank'
          rel='noreferrer'
          className={classnames([styles.agreementLink, styles.termsLink])}
        >
          <Trans>Download Terms & Conditions</Trans>
        </a>

        <Typography>
          <Trans>
            I have read and agreed to the Terms and Conditions &{' '}
            <a
              href={privacyPolicyLink}
              target='_blank'
              rel='noreferrer'
              className={styles.agreementLink}
            >
              Privacy Policies
            </a>
          </Trans>
        </Typography>

        <div className={styles.agreementButtons}>
          <Button
            variant='secondary'
            onClick={onLogout}
            className={styles.logoutButton}
          >
            <Trans>Log Out</Trans>
          </Button>

          <Button onClick={onAgree}>
            <Trans>I Agree</Trans>
          </Button>
        </div>
      </div>
    </WindowBackground>
  );
};

const usePreview = () => {
  const [numPages, setNumPages] = useState(null);

  const { data: termsFile } = useLegalAgreementsFile('tandc');

  const onLoadSuccess = useCallback(({ numPages }) => {
    setNumPages(numPages);
  }, []);

  return {
    numPages,
    termsFile,
    onLoadSuccess,
  };
};

export default memo(Agreement);
