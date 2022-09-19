import React, { useMemo, useCallback } from 'react';
import { useSelector } from 'react-redux';
import { Button } from 'reactstrap';

import PropTypes from 'prop-types';
import { intersection } from 'lodash';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { AGENCY_ADMINISTRATORS, AGENCY_MANAGERS } from '@constants';

import ModalForm from '../ModalForm';
import FormInputsJobAgencyContract from './FormInputsJobAgencyContract';
import FormPreviewJobAgency from './FormPreviewJobAgencyContract';

ModalFormJobAgencyContract.propTypes = {
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  isPreview: PropTypes.bool,
  editingId: PropTypes.number,
  onClosed: PropTypes.func,
  onSaved: PropTypes.func,
  onEdit: PropTypes.func,
};

const renderInputs = (props) => <FormInputsJobAgencyContract {...props} />;

const renderPreview = (props) => <FormPreviewJobAgency {...props} />;

const wrapper = withI18n();

function ModalFormJobAgencyContract(props) {
  const { i18n, editingId, onClosed, onSaved, onEdit } = props;

  const groups = useSelector((state) => state.user.groups);

  const isWriteForbidden = useMemo(
    () => intersection(groups, [AGENCY_ADMINISTRATORS, AGENCY_MANAGERS]).length < 1,
    [groups]
  );

  const isPreview = isWriteForbidden || props.isPreview;

  const renderButtons = useCallback(
    (form, makeOnSubmit, defaultButtonAttr) => (
      <div>
        {isPreview && !isWriteForbidden ? (
          <Button onClick={onEdit} color='primary'>
            {i18n._(t`Edit`)}
          </Button>
        ) : null}
        {!isPreview ? (
          <Button {...defaultButtonAttr} color='primary'>
            {i18n._(t`Save`)}
          </Button>
        ) : null}
      </div>
    ),
    [onEdit, isPreview, isWriteForbidden, i18n]
  );

  return (
    <ModalForm
      readOperationId='job_agency_contracts_read'
      operationId='job_agency_contracts_update'
      editingId={editingId}
      formId='job-agency-contract'
      title={i18n._(t`Job Contract`)}
      inputs={isPreview ? renderPreview : renderInputs}
      buttons={renderButtons}
      onClosed={onClosed}
      onSaved={onSaved}
    />
  );
}

export default wrapper(ModalFormJobAgencyContract);
