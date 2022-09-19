import React from 'react';
import { Button } from 'reactstrap';

import { Trans } from '@lingui/macro';

import { downloadFile } from '@utils/files';

export default class CandidateResumeDownloadButton extends React.Component {
  handleDownload = async () => {
    const { candidateId } = this.props;
    await downloadFile('candidates_get_file', 'resume', candidateId);
  };

  render() {
    return (
      <Button type='button' color='primary' onClick={this.handleDownload}>
        <Trans>Download Resume</Trans>
      </Button>
    );
  }
}
