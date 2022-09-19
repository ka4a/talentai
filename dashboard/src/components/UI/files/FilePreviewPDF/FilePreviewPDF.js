import React, { PureComponent } from 'react';
import { ModalBody } from 'reactstrap';
import { Document, Page } from 'react-pdf';

import _ from 'lodash';
import PropTypes from 'prop-types';

import { client } from '@client';

import Loading from '../../Loading';

import styles from './FilePreviewPDF.module.scss';

class FilePreviewPDF extends PureComponent {
  static propTypes = {
    id: PropTypes.number.isRequired,
    operationId: PropTypes.string.isRequired,
    ftype: PropTypes.string,
  };

  static defaultProps = {
    operationId: null,
  };

  state = {
    isLoading: false,
    pageCount: 0,
    error: null,
    file: null,
  };

  async fetchFile() {
    const { operationId, id, ftype } = this.props;
    if (!id) return;
    this.setState({ isLoading: true });
    try {
      const { data } = await client.execute({
        operationId,
        parameters: { id, ftype },
      });
      this.setState({ file: data, isLoading: false });
      this.updateModalWidth();
    } catch (error) {
      this.setState({ isLoading: false, error });
    }
  }

  async componentDidMount() {
    const element = this.containerRef.current;
    if (element) {
      window.addEventListener('resize', this.updateModalWidth);
      await this.fetchFile(this.props.parameters);
    }
  }

  async componentDidUpdate(prevProps) {
    const { id, ftype } = this.props;
    if (prevProps.id !== id || prevProps.ftype !== ftype) {
      await this.fetchFile();
    }
  }

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
        this.setState({ pageWidth: element.offsetWidth });
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

  renderPage = (pageNumber) => (
    <ModalBody key={`resume_${pageNumber}`} className={styles.page}>
      <Page pageNumber={pageNumber} width={this.state.pageWidth} />
    </ModalBody>
  );

  render() {
    const { pageCount, file, isLoading } = this.state;
    return (
      <div className='w-100' ref={this.containerRef}>
        {isLoading ? (
          <ModalBody className={styles.loading}>
            <Loading />
          </ModalBody>
        ) : (
          <Document file={file} onLoadSuccess={this.handleLoadSuccess}>
            {pageCount > 0 ? _.range(1, pageCount + 1).map(this.renderPage) : null}
          </Document>
        )}
      </div>
    );
  }
}

export default React.memo(FilePreviewPDF);
