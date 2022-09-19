import React, { useCallback, memo } from 'react';

import PropTypes from 'prop-types';
import { t, Trans } from '@lingui/macro';
import classnames from 'classnames';

import { Switch, Typography } from '@components';
import { getCareerSiteUrl } from '@utils';

import styles from '../CompanySettings.module.scss';

function CareerPanel({ setValue, FormInput, form }) {
  const { isCareerSiteEnabled } = form;

  const toggleCareerSwitch = useCallback(
    async (checked) => {
      setValue('isCareerSiteEnabled', checked);
    },
    [setValue]
  );

  return (
    <>
      <Typography variant='subheading'>
        <Trans>Career Site</Trans>
      </Typography>

      <Typography className={styles.topGap}>
        <Trans>
          Branded public-facing page listing all the jobs you have published externally.
        </Trans>
      </Typography>

      <div className={styles.topGap}>
        <Switch
          label={t`Career Site`}
          checked={isCareerSiteEnabled}
          onChange={toggleCareerSwitch}
        />
      </div>

      <div className={classnames([styles.topGap, styles.careerSite])}>
        <FormInput
          type='stuffed'
          name='careerSiteSlug'
          label={t`Career Site URL`}
          disabled={!isCareerSiteEnabled}
          required
          beforeInput={
            <Typography variant='caption' className={styles.host}>
              {getCareerSiteUrl()}
            </Typography>
          }
        />
      </div>
    </>
  );
}

CareerPanel.propTypes = {
  FormInput: PropTypes.func.isRequired,
  form: PropTypes.shape({
    careerSiteSlug: PropTypes.string,
    isCareerSiteEnabled: PropTypes.bool,
  }).isRequired,
  setValue: PropTypes.func.isRequired,
};

export default memo(CareerPanel);
