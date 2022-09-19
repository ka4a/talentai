import React, { memo } from 'react';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { Typography } from '@components';
import { getFileName, getFileExtension } from '@utils';

import styles from './FileThumbnail.module.scss';

const FileThumbnail = (props) => {
  const { id, title, file, thumbnail, children } = props;

  const handleDownload = () => props.onDownload?.(id);

  const onClick = props.onClick || handleDownload;

  const filename = getFileName(file);
  const ext = getFileExtension(file);

  return (
    <div className={styles.thumbnailWrapper}>
      <div className={styles.thumbnail}>
        {thumbnail ? (
          <img onClick={onClick} height={185} width={130} src={thumbnail} alt='' />
        ) : (
          <div onClick={onClick} className={styles.thumbnailStub}>
            <span className='fs-30'>{ext}</span>
          </div>
        )}

        {children}
      </div>

      {title ? (
        <Typography variant='caption' className={styles.caption}>
          <Trans>{title}</Trans>
        </Typography>
      ) : (
        <span className={styles.thumbnailStub__name} title={title || filename}>
          {filename}
        </span>
      )}
    </div>
  );
};

FileThumbnail.propTypes = {
  id: PropTypes.number.isRequired,
  onClick: PropTypes.func,
  onDownload: PropTypes.func,
  thumbnail: PropTypes.string,
  file: PropTypes.string.isRequired,
  ftype: PropTypes.string,
  title: PropTypes.string,
};

FileThumbnail.defaultProps = {
  file: '',
  title: '',
  thumbnail: '',
  onClick: null,
  onDownload: null,
};

export default memo(FileThumbnail);
