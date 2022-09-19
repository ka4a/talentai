import React from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { Trans } from '@lingui/macro';

import FileThumbnail from '../FileThumbnail';

import styles from './NewFileThumbnail.module.scss';

const propTypes = {
  error: PropTypes.bool,
  id: PropTypes.number.isRequired,
  onRemove: PropTypes.func,
};

const defaultProps = {
  error: false,
  onRemove: null,
};

function NewFileThumbnail(props) {
  const { id, file, onRemove, error, children } = props;

  return (
    <FileThumbnail id={id} onRemove={onRemove} file={file}>
      <div className={classnames(styles.tag, 'bg-primary', { 'bg-danger': error })}>
        {error ? <Trans>Error</Trans> : <Trans>New</Trans>}
      </div>
      {children}
    </FileThumbnail>
  );
}

NewFileThumbnail.propTypes = propTypes;
NewFileThumbnail.defaultProps = defaultProps;

export default NewFileThumbnail;
