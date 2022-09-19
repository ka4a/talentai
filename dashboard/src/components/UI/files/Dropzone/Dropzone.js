import React, { useCallback, useState, memo } from 'react';
import ReactDropzone from 'react-dropzone';
import { toast } from 'react-toastify';

import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';
import classNames from 'classnames';

import Typography from '@components/UI/Typography';
import Button from '@components/UI/Button';

import { getAcceptedFileType } from '../FileInput/logicHooks';

import styles from './Dropzone.module.scss';

function Dropzone(props) {
  const { fileMaxSize, acceptedFileType, onDrop, limit } = props;

  const [isDragOver, setIsDragOver] = useState(false);

  const handleDragEnter = useCallback(() => setIsDragOver(true), []);
  const handleDragLeave = useCallback(() => setIsDragOver(false), []);
  const handleDrop = useCallback(
    (files) => {
      setIsDragOver(false);
      onDrop?.(files);
    },
    [onDrop]
  );

  const handleDropRejected = useCallback(() => {
    toast.error(
      <Trans>
        File uploaded must be an accepted file type (
        {getAcceptedFileType(acceptedFileType).join(', ')}) and size less than{' '}
        {humanFileSize(fileMaxSize)}
      </Trans>,
      {
        position: 'bottom-center',
        autoClose: false,
        className: 'toast-alert',
        closeOnClick: true,
      }
    );
  }, [fileMaxSize, acceptedFileType]);

  return (
    <ReactDropzone
      maxSize={fileMaxSize}
      accept={getAcceptedFileType(acceptedFileType)}
      onDrop={handleDrop}
      onDropRejected={handleDropRejected}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
    >
      {({ getRootProps, getInputProps }) => (
        <div
          {...getRootProps()}
          className={classNames(styles.root, { [styles.hover]: isDragOver })}
        >
          <input {...getInputProps()} />

          <Typography className={styles.text}>
            {limit === 1 ? (
              <Trans>Drag and Drop a file to upload</Trans>
            ) : (
              <Trans>Drag and Drop your files to upload</Trans>
            )}
          </Typography>

          <Button variant='secondary'>
            <Trans>Browse</Trans>
          </Button>
        </div>
      )}
    </ReactDropzone>
  );
}

const SIZE_UNITS = ['B', 'kB', 'MB', 'GB', 'TB'];
const MAX_SIZE_UNIT = SIZE_UNITS[SIZE_UNITS.length - 1];

const humanFileSize = (size) => {
  let readableSize = size;
  let unit;
  for (unit of SIZE_UNITS) {
    if (readableSize < 1024 || unit === MAX_SIZE_UNIT) break;
    readableSize = readableSize / 1024;
  }
  return `${Number(readableSize.toFixed(2))} ${unit}`;
};

const MAX_FILE_SIZE = 10485760;

Dropzone.propTypes = {
  fileMaxSize: PropTypes.number,
  acceptedFileType: PropTypes.oneOf(['image', 'resume', 'other']),
  onDrop: PropTypes.func.isRequired,
  limit: PropTypes.number,
};

Dropzone.defaultProps = {
  limit: 1,
  fileMaxSize: MAX_FILE_SIZE,
};

export default memo(Dropzone);
