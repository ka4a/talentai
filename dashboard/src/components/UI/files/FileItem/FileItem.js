import React, { memo } from 'react';

import PropTypes from 'prop-types';
import classnames from 'classnames';
import { t } from '@lingui/macro';

import { getFilePathWithoutParams } from '@utils';
import { ReactComponent as TrashCan } from '@images/icons/trash-can.svg';

import LabeledInput from '../../LabeledInputs/LabeledInput';
import Typography from '../../Typography';

import styles from './FileItem.module.scss';

const FileItem = (props) => {
  const {
    file: sourceFile,
    onChangeTitle,
    onDownloadFile,
    onDeleteFile,
    renderCustomTitle,
    withoutTitle,
    error,
  } = props;

  // ftype here is available only on Resume (Candidate Create/Edit)
  const { id, localId, title, file, name, ftype } = sourceFile;

  // "file" field is available for uploaded files
  // "name" field is available for new files
  const isNewFile = Boolean(name);
  const fileName = isNewFile
    ? getFilePathWithoutParams(name)
    : file.split('/').splice(-1)[0].split('?')[0];

  const renderTitle = () => {
    if (withoutTitle) return null;

    if (renderCustomTitle) return renderCustomTitle(sourceFile);

    return (
      <div className={styles.titleWrapper}>
        <LabeledInput
          label={t`Title`}
          value={title}
          onChange={(e) => onChangeTitle(e, id)}
          wrapperClassName={styles.input}
        />

        {!title && error && (
          <Typography variant='caption' className={styles.titleError}>
            {error}
          </Typography>
        )}
      </div>
    );
  };

  return (
    <div className={styles.wrapper}>
      {renderTitle()}

      <div
        className={classnames(styles.nameWrapper, {
          [styles.withoutTitle]: withoutTitle,
        })}
      >
        <Typography
          variant='caption'
          className={classnames(styles.itemName, {
            [styles.downloadable]: onDownloadFile,
          })}
          onClick={() => onDownloadFile?.(id, ftype)}
        >
          {fileName}
        </Typography>

        <TrashCan
          className={styles.delete}
          onClick={() => onDeleteFile({ id, localId, ftype, file })}
        />
      </div>
    </div>
  );
};

const LocalPropTypes = {
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
};

FileItem.propTypes = {
  file: PropTypes.shape({
    id: LocalPropTypes.id,
    localId: LocalPropTypes.id,
    title: PropTypes.string,
    file: PropTypes.string,
    name: PropTypes.string,
    ftype: PropTypes.string,
  }).isRequired,
  onChangeTitle: PropTypes.func,
  onDownloadFile: PropTypes.func,
  onDeleteFile: PropTypes.func,
  renderCustomTitle: PropTypes.func,
  withoutTitle: PropTypes.bool.isRequired,
  error: PropTypes.string,
};

FileItem.defaultProps = {
  onChangeTitle: () => {},
  onDeleteFile: () => {},
  onDownloadFile: null,
  renderCustomTitle: null,
  error: null,
};

export default memo(FileItem);
