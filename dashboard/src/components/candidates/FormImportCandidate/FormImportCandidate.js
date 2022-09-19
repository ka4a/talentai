import React, { useState } from 'react';
import { TabContent, TabPane, Nav, Input, Button, Label, FormGroup } from 'reactstrap';
import { connect } from 'react-redux';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { Trans } from '@lingui/macro';

import LinkedInImport from '../LinkedInImport';
import Typography from '../../UI/Typography';
import ZohoImport from '../../ZohoImport';
import TabItem from './TabItem';
import JobLonglistImport from '../../jobs/JobLonglistImport';

import styles from './FormImportCandidate.module.scss';

const wrapper = connect((state) => ({
  hasZohoIntegration: _.get(state, 'user.profile.org.hasZohoIntegration', false),
}));

const TABS = {
  linkedIn: 'linkedIn',
  zoho: 'zoho',
  job: 'job',
};

const getInitialTab = (hasZohoIntegration) => {
  if (hasZohoIntegration) {
    return TABS.zoho;
  } else if (window.extInstalled) {
    return TABS.linkedIn;
  } else {
    return TABS.job;
  }
};

function FormImportCandidate(props) {
  const { jobId, hasZohoIntegration, onSuccess, onError, stage, onClosed } = props;
  const [tab, setTab] = useState(getInitialTab(hasZohoIntegration));

  const showJobTab = stage === 'longlist';

  const tabContent = ({ name, inputRef, onConfirm, isLoading }) => (
    <div className={styles.tabContent}>
      <FormGroup>
        <Label for={name}>
          <Trans>URL</Trans>
        </Label>
        <Input name={name} bsSize='lg' disabled={isLoading} innerRef={inputRef} />
      </FormGroup>

      <div className={styles.actions}>
        <Button color='primary' disabled={isLoading} onClick={onConfirm}>
          <Typography variant='button'>
            <Trans>Confirm</Trans>
          </Typography>
        </Button>
      </div>
    </div>
  );

  return (
    <div>
      <Nav tabs>
        <TabItem
          show={hasZohoIntegration}
          tabId={TABS.zoho}
          onSelect={setTab}
          activeTabId={tab}
        >
          <Trans>Zoho</Trans>
        </TabItem>
        <TabItem
          show={window.extInstalled}
          tabId={TABS.linkedIn}
          onSelect={setTab}
          activeTabId={tab}
        >
          <Trans>LinkedIn</Trans>
        </TabItem>
        <TabItem show={showJobTab} tabId={TABS.job} onSelect={setTab} activeTabId={tab}>
          <Trans>Job</Trans>
        </TabItem>
      </Nav>
      <TabContent activeTab={tab}>
        <TabPane tabId={TABS.zoho}>
          <ZohoImport onSuccess={onSuccess} onError={onError}>
            {tabContent}
          </ZohoImport>
        </TabPane>
        <TabPane tabId={TABS.linkedIn}>
          <LinkedInImport jobId={jobId} onSuccess={onSuccess} onError={onError}>
            {tabContent}
          </LinkedInImport>
        </TabPane>
        <TabPane tabId={TABS.job}>
          <JobLonglistImport jobId={jobId} onSuccess={onClosed} onError={onError} />
        </TabPane>
      </TabContent>
    </div>
  );
}

FormImportCandidate.propTypes = {
  jobId: PropTypes.number,
  hasZohoIntegration: PropTypes.bool,
  onSuccess: PropTypes.func,
  onClosed: PropTypes.func,
};

FormImportCandidate.defaultProps = {
  jobId: null,
  hasZohoIntegration: false,
  onSuccess() {},
  onClosed() {},
};

export default wrapper(FormImportCandidate);
