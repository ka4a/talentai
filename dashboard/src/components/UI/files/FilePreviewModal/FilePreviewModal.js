import React, { memo, cloneElement } from 'react';
import { useToggle } from 'react-use';
import { Modal } from 'reactstrap';

import PropTypes from 'prop-types';

import { getFileExtension, getFileName } from '@utils';

import PaginatedFilePreviewPDF from '../PaginatedFilePreviewPDF';

FilePreviewModal.propTypes = {
  id: PropTypes.number.isRequired,
  ftype: PropTypes.string,
  params: PropTypes.object,
  file: PropTypes.string,
  preview: PropTypes.string,
  children: PropTypes.node.isRequired,
  onDownload: PropTypes.func.isRequired,
  operationId: PropTypes.string.isRequired,
  previewOperationId: PropTypes.string,
};

function FilePreviewModal(props) {
  const {
    children,
    operationId,
    previewOperationId,
    ftype,
    id,
    file,
    onDownload,
    params,
    preview,
  } = props;
  const [isOpen, toggle] = useToggle(false);

  const isPreviewAvailable =
    (previewOperationId && preview) || getFileExtension(file) === 'pdf';

  if (isPreviewAvailable)
    return (
      <>
        {cloneElement(children, { onClick: toggle })}
        <Modal isOpen={isOpen} toggle={toggle} size='lg'>
          <PaginatedFilePreviewPDF
            onDownload={onDownload}
            params={params}
            title={getFileName(file)}
            operationId={previewOperationId || operationId}
            ftype={ftype}
            id={id}
          />
        </Modal>
      </>
    );

  return children;
}

export default memo(FilePreviewModal);
