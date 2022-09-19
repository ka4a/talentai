import React from 'react';
import { Col, FormGroup, Input, Row } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { withI18n } from '@lingui/react';
import { Trans, t } from '@lingui/macro';

import ModalForm from './ModalForm';

const FIELDS = [
  'firstName',
  'lastName',
  'currentCompany',
  'currentPosition',
  'currentLocation',
  'email',
  'websiteUrl',
  'twitterUrl',
  'githubUrl',
];
const FIELD_TITLES = {
  firstName: <Trans>First Name</Trans>,
  lastName: <Trans>Last Name(s)</Trans>,
  currentCompany: <Trans>Current Employer</Trans>,
  currentPosition: <Trans>Current Job Title</Trans>,
  currentLocation: <Trans>Current Location</Trans>,
  email: <Trans>Email (Primary)</Trans>,
  websiteUrl: <Trans>Personal Website URL</Trans>,
  twitterUrl: <Trans>Twitter URL</Trans>,
  githubUrl: <Trans>GitHub URL</Trans>,
};

class DiffInput extends React.Component {
  state = { replaced: false };

  onReplaceChange = (e) => {
    const { checked } = e.target;
    const { form, name, setValue } = this.props;

    setValue(name, checked ? form.patchData[name] : form.candidate[name]);

    this.setState({ replaced: checked });
  };

  render() {
    const { form, name, title, setValue } = this.props;
    const { replaced } = this.state;

    return (
      <FormGroup tag='fieldset'>
        <legend className='col-form-label'>{title}</legend>
        <Row form>
          <Col xs={5}>
            <FormGroup>
              <Input disabled value={form.patchData[name]} />
            </FormGroup>
          </Col>
          <Col xs={2}>
            <div className='merge-modal-checkbox-container'>
              <Input type='checkbox' value={replaced} onChange={this.onReplaceChange} />{' '}
            </div>
          </Col>
          <Col xs={5}>
            <FormGroup>
              <Input
                name={name}
                id={`${name}Input`}
                value={form[name]}
                onChange={(e) => setValue(name, e.target.value)}
              />
            </FormGroup>
          </Col>
        </Row>
      </FormGroup>
    );
  }
}

class DataMergeModal extends React.Component {
  getInputs = ({ form, setValue }) => (
    <div>
      <Row form>
        <Col xs={5}>
          <span className='h4'>
            <Trans>Crawled Data</Trans>
          </span>
        </Col>
        <Col xs={{ size: 5, offset: 2 }}>
          <span className='h4'>
            <Trans>Candidate Data</Trans>
          </span>
        </Col>
      </Row>

      {_.map(FIELDS, (name) => {
        if (!form.patchData[name] || form.candidate[name] === form.patchData[name]) {
          return null;
        }

        return (
          <DiffInput
            key={name}
            form={form}
            name={name}
            setValue={setValue}
            title={FIELD_TITLES[name]}
          />
        );
      })}
    </div>
  );

  render() {
    const { editingId, onSaved, onClosed } = this.props;

    return (
      <ModalForm
        formId='candidateDataMerge'
        title={this.props.i18n._(t`Data Merge`)}
        readOperationId='candidates_linkedin_data_get_candidate_data'
        operationId='candidates_partial_update'
        processReadObject={function (obj) {
          /* copy candidate data so we have original values */
          const patchKeys = _.keys(obj.patchData);
          const fieldsData = _.mapKeys(obj.candidate, function (value, key) {
            if (!_.includes(patchKeys, key)) {
              return null;
            }

            return key;
          });

          return {
            id: obj.candidate.id,
            ...fieldsData,
            ...obj,
          };
        }}
        processFormState={function (form) {
          return _.omit(form, ['candidate', 'patchData']);
        }}
        editingId={editingId}
        onSaved={onSaved}
        onClosed={onClosed}
        size='lg'
        inputs={this.getInputs}
      />
    );
  }
}

DataMergeModal.propTypes = {
  editingId: PropTypes.any,
  onSaved: PropTypes.func,
  onClosed: PropTypes.func,
};

export default withI18n()(DataMergeModal);
