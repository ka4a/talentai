import React, { PureComponent } from 'react';
import { Button, ModalBody, ModalHeader } from 'reactstrap';
import { Document, Page } from 'react-pdf';

import _ from 'lodash';
import PropTypes from 'prop-types';
import { Trans } from '@lingui/macro';

import { withReqStatus } from '../../ReqStatus';

class PaginatedFilePreviewPDF extends PureComponent {
  static propTypes = {
    id: PropTypes.number.isRequired,
    operationId: PropTypes.string.isRequired,
    ftype: PropTypes.string,
    renderIfLoaded: PropTypes.func.isRequired,
    title: PropTypes.string,
    wrappedExecute: PropTypes.func.isRequired,
    params: PropTypes.object,
  };

  static defaultProps = {
    operationId: null,
    params: null,
  };

  state = {
    pageCount: 1,
    currentPage: 1,
    file: null,
  };

  async fetchFile() {
    const { operationId, id, ftype, wrappedExecute, params } = this.props;
    if (!id) return;
    const { data } = await wrappedExecute({
      operationId,
      parameters: { id, ftype, ...params },
    });
    this.setState({ file: data });
    this.updateModalWidth();
  }

  async componentDidMount() {
    const element = this.containerRef.current;
    if (element) {
      window.addEventListener('resize', this.updateModalWidth);
      await this.fetchFile(this.props.parameters);
    }
  }

  async componentDidUpdate(prevProps) {
    const { id, ftype, params } = this.props;
    const areSameParams =
      prevProps.id === id &&
      prevProps.ftype === ftype &&
      _.isEqual(prevProps.params, params);
    if (!areSameParams) {
      await this.fetchFile();
    }
  }

  handleDownload = () => {
    const { onDownload, id } = this.props;
    if (!onDownload) return;
    onDownload(id);
  };

  makeChangeState = (callback) => () => this.setState(callback);
  nextPage = this.makeChangeState((state) => ({ currentPage: state.currentPage + 1 }));
  prevPage = this.makeChangeState((state) => ({ currentPage: state.currentPage - 1 }));

  componentWillUnmount() {
    const element = this.containerRef.current;
    if (element) {
      window.removeEventListener('resize', this.updateModalWidth);
    }
  }

  containerRef = React.createRef();

  updateModalWidth = _.throttle(
    () => {
      const element = this.containerRef.current;
      if (element && element.offsetWidth !== this.state.pageWidth) {
        this.setState({ pageWidth: element.offsetWidth - 4 });
      }
    },
    500,
    { leading: false, trailing: true }
  );

  handleLoadSuccess = (args) => {
    const { numPages } = args;
    this.setState({
      isLoaded: true,
      pageCount: numPages,
    });
  };

  render() {
    const { renderIfLoaded, title } = this.props;
    const { pageCount, pageWidth, currentPage, file } = this.state;
    return (
      <div className='w-100'>
        <ModalHeader tag='span' className='h3' toggle={this.toggle}>
          {title}
        </ModalHeader>

        <ModalBody>
          <div className='w-100' ref={this.containerRef}>
            {renderIfLoaded(() => (
              <>
                <p>
                  <Trans>
                    Page {currentPage} of {pageCount}
                  </Trans>
                </p>
                <div>
                  <Button
                    color='primary'
                    disabled={currentPage === 1}
                    onClick={this.prevPage}
                  >
                    <Trans>Prev</Trans>
                  </Button>{' '}
                  <Button
                    color='primary'
                    disabled={currentPage === pageCount}
                    onClick={this.nextPage}
                  >
                    <Trans>Next</Trans>
                  </Button>
                </div>
                <Document
                  className='mt-4 border border-secondary'
                  file={file}
                  onLoadSuccess={this.handleLoadSuccess}
                >
                  {pageWidth ? (
                    <Page pageNumber={currentPage} width={pageWidth} />
                  ) : null}
                </Document>

                <div className='text-center mt-4'>
                  <Button type='button' color='primary' onClick={this.handleDownload}>
                    <Trans>Download</Trans>
                  </Button>
                </div>
              </>
            ))}
          </div>
        </ModalBody>
      </div>
    );
  }
}

export default withReqStatus(PaginatedFilePreviewPDF);
