import React, { memo, useCallback, useMemo } from 'react';
import { useCopyToClipboard } from 'react-use';

import PropTypes from 'prop-types';
import { t, Trans } from '@lingui/macro';
import classNames from 'classnames';

import {
  Badge,
  Button,
  SideButtonInput,
  Switch,
  Typography,
  WindowBackground,
} from '@components';
import formStyles from '@styles/form.module.scss';

import { POSTING_STATUSES } from '../../constants';

import styles from './JobPostingBlock.module.scss';

function JobPostingBlock(props) {
  const {
    title,
    status,
    statusInfoMap,
    onEdit,
    onSwitchEnabled,
    isEditable,
    isEnabled,
    canEnable,
    link,
  } = props;

  const [, copyToClipboard] = useCopyToClipboard();

  const statusInfo = statusInfoMap[status] ?? statusInfoMap?.disabled ?? {};

  const shouldShowBadgeForEditable = useShouldShowBadgeForEditable(status);

  const copyLink = useCallback(
    (event, inputValue) => {
      copyToClipboard(inputValue);
    },
    [copyToClipboard]
  );

  return (
    <WindowBackground className={formStyles.formContainerWidePadded}>
      <div className={classNames(formStyles.title, styles.header)}>
        <div className={styles.titleWrapper}>
          <Typography variant='h3'>{title}</Typography>
          {isEditable && (
            <Switch
              checked={isEnabled}
              onChange={onSwitchEnabled}
              disabled={!canEnable}
            />
          )}
          {(shouldShowBadgeForEditable || !isEditable) && (
            <Badge text={statusInfo.title} variant={statusInfo.variant} />
          )}
        </div>
        {isEditable && (
          <Button variant='secondary' onClick={onEdit}>
            <Trans>Edit</Trans>
          </Button>
        )}
      </div>
      {(isEditable || isEnabled) && (
        <div className={formStyles.title}>{statusInfo.description}</div>
      )}
      {isEnabled && (
        <div className={classNames(formStyles.title, styles.linkWrapper)}>
          <SideButtonInput
            isReadOnly
            value={link}
            onButtonClick={copyLink}
            buttonText={t`Copy`}
          />
        </div>
      )}
    </WindowBackground>
  );
}

function useShouldShowBadgeForEditable(status) {
  return useMemo(() => !SWITCH_STATUSES.includes(status), [status]);
}

const SWITCH_STATUSES = [POSTING_STATUSES.enabled, POSTING_STATUSES.disabled];

JobPostingBlock.propTypes = {
  status: PropTypes.oneOf(Object.values(POSTING_STATUSES)),
  statusInfoMap: PropTypes.objectOf(
    PropTypes.shape({
      title: PropTypes.string,
      description: PropTypes.node,
      variant: PropTypes.string,
    })
  ),
  title: PropTypes.node.isRequired,
  onEdit: PropTypes.func.isRequired,
  onSwitchEnabled: PropTypes.func.isRequired,
  isEditable: PropTypes.bool,
  isEnabled: PropTypes.bool,
  canEnable: PropTypes.bool,
  link: PropTypes.string,
};

JobPostingBlock.defaultProps = {
  statusVariant: 'normal',
  isEditable: false,
  isEnabled: false,
  canEnable: false,
  link: '',
};

export default memo(JobPostingBlock);
