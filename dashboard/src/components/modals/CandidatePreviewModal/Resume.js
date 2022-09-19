import React from 'react';

import PropTypes from 'prop-types';

import { FilePreviewPDF } from '@components';

const propTypes = {
  candidateId: PropTypes.number,
};

const defaultProps = {
  candidateId: null,
};

const Resume = ({ candidateId }) => (
  <FilePreviewPDF operationId='candidates_get_file' id={candidateId} ftype='resume' />
);

Resume.propTypes = propTypes;
Resume.defaultProps = defaultProps;

export default React.memo(Resume);
