import React, { Component } from 'react';
import { Document, Page } from 'react-pdf';
import { Button, Modal, ModalBody, ModalHeader } from 'reactstrap';

import { Trans } from '@lingui/macro';

import { client } from '@client';

import CandidateResumeDownloadButton from './CandidateResumeDownloadButton';
import ReqStatus, {
  fetchLoadingWrapper,
  getDefaultReqState,
} from '../ReqStatus/ReqStatus';

export class CandidateResumePreview extends Component {
  state = {
    ...getDefaultReqState(),
    modal: true,
    width: null,
    pdfLoaded: false,
    numPages: null,
    pageNumber: 1,
  };
  file = null;

  onDocumentLoadSuccess = ({ numPages }) => {
    this.setState({ numPages, pdfLoaded: true });
  };

  toggle = () => this.setState({ modal: !this.state.modal });
  onClosed = () => {
    // TODO: hack to avoid bug
    // https://github.com/reactstrap/reactstrap/issues/1279
    this.setState({ modal: false }, () => {
      this.props.onClosed();
    });
  };

  fetchData = fetchLoadingWrapper(() =>
    client
      .execute({
        operationId: 'candidates_get_file',
        parameters: { id: this.props.candidateId, ftype: 'resume' },
      })
      .then((response) => {
        this.file = response.data;
      })
  ).bind(this);

  componentDidMount() {
    this.fetchData();
  }

  onPrev = () => {
    this.setState((state) => ({ pageNumber: state.pageNumber - 1 }));
  };
  onNext = () => {
    this.setState((state) => ({ pageNumber: state.pageNumber + 1 }));
  };

  onWidthElMount = (el) => {
    if (el) {
      this.setState({ width: el.offsetWidth - 2 }); // 2px for border
    }
  };

  render() {
    const { candidateId } = this.props;
    const { reqStatus, modal, width, pageNumber, numPages } = this.state;

    return (
      <Modal isOpen={modal} onClosed={this.onClosed} toggle={this.toggle} size='lg'>
        <ModalHeader tag='span' className='h3' toggle={this.toggle}>
          <Trans>Resume Preview</Trans>
        </ModalHeader>

        {reqStatus.render ? (
          <ModalBody>
            <ReqStatus inline {...reqStatus} />
          </ModalBody>
        ) : null}

        {!reqStatus.render ? (
          <ModalBody>
            <div className='w-100' ref={this.onWidthElMount}>
              {''}
            </div>
            <p>
              <Trans>
                Page {pageNumber} of {numPages}
              </Trans>
            </p>
            <div>
              <Button color='primary' disabled={pageNumber === 1} onClick={this.onPrev}>
                <Trans>Prev</Trans>
              </Button>{' '}
              <Button
                color='primary'
                disabled={pageNumber === numPages}
                onClick={this.onNext}
              >
                <Trans>Next</Trans>
              </Button>
            </div>
            <Document
              className='mt-4 border border-secondary'
              file={this.file}
              onLoadSuccess={this.onDocumentLoadSuccess}
            >
              {width !== null ? <Page pageNumber={pageNumber} width={width} /> : null}
            </Document>

            <div className='text-center mt-4'>
              <CandidateResumeDownloadButton candidateId={candidateId} />
            </div>
          </ModalBody>
        ) : null}
      </Modal>
    );
  }
}
