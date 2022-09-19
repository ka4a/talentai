import React from 'react';

import PropTypes from 'prop-types';

import { CandidateResumePreview } from './CandidateResumePreview';
import FileThumbnail from '../FileThumbnail';

export default class CandidateResumePreviewButton extends React.Component {
  static propTypes = {
    onRemove: PropTypes.func.isRequired,
    file: PropTypes.shape({
      thumbnail: PropTypes.string,
      file: PropTypes.string.isRequired,
      id: PropTypes.number.isRequired,
    }),
  };

  state = { preview: false };

  onPreview = () => {
    this.setState({ preview: true });
  };

  onPreviewClosed = () => {
    this.setState({ preview: false });
  };

  render() {
    const { preview } = this.state;
    const { file, onRemove } = this.props;

    return (
      <>
        <FileThumbnail {...file} onClick={this.onPreview} onRemove={onRemove} />
        {preview ? (
          <CandidateResumePreview
            candidateId={this.props.file.id}
            onClosed={this.onPreviewClosed}
          />
        ) : null}
      </>
    );
  }
}
