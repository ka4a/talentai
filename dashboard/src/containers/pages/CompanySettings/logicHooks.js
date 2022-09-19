import React, { useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { useDispatch } from 'react-redux';

import { omit } from 'lodash';
import { Trans } from '@lingui/macro';

import { getCareerSiteName, isDialogConfirmed, makeSaveFilesForForm } from '@utils';
import { ButtonBar, Typography } from '@components';
import styles from '@styles/form.module.scss';
import { readUser } from '@actions';

import Inputs from './components/Inputs';
import openEnableCareerSite from './utils/openEnableCareerSite';
import openDisableCareerSite from './utils/openDisableCareerSite';

const initialState = {
  companyNameEN: '',
  companyNameJP: '',
  website: '',
  country: '',
  functionFocus: [],
  logo: null,
  newLogo: null,
  isCareerSiteEnabled: false,
  careerSiteSlug: '',
};

export const saveFiles = makeSaveFilesForForm(
  (state) => {
    const toUpload = [];
    if (state.newLogo)
      toUpload.push({
        file: state.newLogo,
        operationId: 'client_settings_upload_logo',
        getParams: () => ({
          ftype: 'photo',
          file: state.newLogo.file,
        }),
      });
    return toUpload;
  },
  (newFiles) => {
    return newFiles.reduce((patch, upload) => {
      patch.newLogo = upload.file;
      return patch;
    }, {});
  }
);

const useFormProcessing = () => {
  const processReadObject = useCallback(
    (companySettings) => ({
      ...companySettings,
      careerSiteSlug:
        companySettings.careerSiteSlug || getCareerSiteName(companySettings.name),
      // logic fields
      wasCareerSiteEnabled: companySettings.isCareerSiteEnabled,
    }),
    []
  );

  const processFormState = useCallback((form) => omit(form, ['logo']), []);

  const dispatch = useDispatch();

  const onSubmitDone = useCallback(
    async (...props) => {
      dispatch(readUser());
      await saveFiles(...props);
    },
    [dispatch]
  );

  const checkFormStateBeforeSave = useCallback(async (form) => {
    const { wasCareerSiteEnabled, isCareerSiteEnabled } = form;

    if (wasCareerSiteEnabled !== isCareerSiteEnabled) {
      const openConfirmCareerSiteStatus = isCareerSiteEnabled
        ? openEnableCareerSite
        : openDisableCareerSite;
      return await isDialogConfirmed(openConfirmCareerSiteStatus());
    }
    return true;
  }, []);

  return {
    initialState,
    onSubmitDone,
    processFormState,
    processReadObject,
    checkFormStateBeforeSave,
  };
};

const useGetElements = () => {
  const history = useHistory();

  const renderHeader = useCallback(
    () => (
      <Typography variant='h1' className={styles.title}>
        <Trans>Company Settings</Trans>
      </Typography>
    ),
    []
  );

  const renderInputs = useCallback(({ FormInput, setValue, form }) => {
    return <Inputs FormInput={FormInput} setValue={setValue} form={form} />;
  }, []);

  const renderButtons = useCallback(
    (form, makeOnSubmit, { disabled }) => (
      <ButtonBar
        onCancel={history.goBack}
        onSave={makeOnSubmit()}
        isDisabled={disabled}
      />
    ),
    [history]
  );

  return {
    header: renderHeader,
    inputs: renderInputs,
    buttons: renderButtons,
  };
};

export { useGetElements, useFormProcessing };
