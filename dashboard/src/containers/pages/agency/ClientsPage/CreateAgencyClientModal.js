import React, { cloneElement } from 'react';
import { Modal, ModalHeader, ModalBody, Row, Button } from 'reactstrap';
import { useToggle } from 'react-use';

import { Trans, t } from '@lingui/macro';
import { withI18n } from '@lingui/react';

import SwaggerForm from '../../../../components/SwaggerForm';

const initialState = {
  name: '',
};

function CreateAgencyClientModal({ children, onClosed, i18n }) {
  const [isOpen, toggle] = useToggle(false);

  const getInputs = ({ FormInputBlock }) => {
    return (
      <div>
        <Row form>
          <FormInputBlock isWide name='name' label={i18n._(t`Name`)} />
        </Row>
      </div>
    );
  };

  const getButtons = (form, makeOnSubmit, defaultButtonAttrs) => {
    return (
      <div className='clearfix'>
        <div className='float-right'>
          <Button {...defaultButtonAttrs} onClick={makeOnSubmit()}>
            <Trans>Create</Trans>
          </Button>
        </div>
      </div>
    );
  };

  return (
    <>
      {cloneElement(children, { onClick: toggle })}
      <Modal isOpen={isOpen} toggle={toggle} onClosed={onClosed}>
        <ModalHeader tag='h2'>
          <Trans>Create Client</Trans>
        </ModalHeader>
        <ModalBody>
          <SwaggerForm
            formId='CreateAgencyClientForm'
            operationId='clients_create'
            inputs={getInputs}
            buttons={getButtons}
            initialState={initialState}
            onSaved={toggle}
          />
        </ModalBody>
      </Modal>
    </>
  );
}

export default withI18n()(CreateAgencyClientModal);
