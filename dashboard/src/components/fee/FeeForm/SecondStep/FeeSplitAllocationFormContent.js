import React, { memo, Component, useCallback } from 'react';
import { connect } from 'react-redux';
import { Col } from 'reactstrap';

import PropTypes from 'prop-types';
import { compose } from 'redux';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import FormSection from '../../../SwaggerFormSection';
import UserOptionsProvider from '../../../UserOptionsProvider';
import FileInput from '../../../UI/files/FileInput';
import FormThumbnailList from '../../FormThumbnailList';

const wrapper = compose(
  memo,
  withI18n(),
  connect((state) => ({
    locale: state.settings.locale,
  }))
);

const LocalPropTypes = {
  component: PropTypes.oneOfType([PropTypes.func, PropTypes.instanceOf(Component)]),
};

FeeSplitAllocationFormContent.propTypes = {
  form: PropTypes.shape({
    shouldSendInvoiceEmail: PropTypes.bool,
    signedAt: PropTypes.string,
    startWorkAt: PropTypes.string,
    consultingFeeType: PropTypes.string,
    contractType: PropTypes.string,
  }).isRequired,
  FormInputBlock: LocalPropTypes.component,
  i18n: PropTypes.shape({
    _: PropTypes.func.isRequired,
  }).isRequired,
  locale: PropTypes.string,
};

function FeeSplitAllocationFormContent(props) {
  const { FormInputBlock, i18n, form, setValue, isDisabled } = props;

  const handleFileRemoved = useCallback(() => {
    setValue('files', []);
  }, [setValue]);

  const userPlaceholder = i18n._(t`Select user`);
  const noFiles = form.files.length + form.newFiles.length === 0;

  return (
    <UserOptionsProvider
      render={(userOptions) => (
        <div className='pt-4'>
          <FormSection title={i18n._(t`Split Allocations`)}>
            <FormInputBlock
              type='select'
              label={i18n._(t`Candidate Owner`)}
              name='candidateOwner'
              options={userOptions}
              placeholder={userPlaceholder}
            />
            <FormInputBlock
              type='percentage'
              label={i18n._(t`Candidate Owner Split`)}
              name='candidateOwnerSplit'
            />
            <FormInputBlock
              type='select'
              label={i18n._(t`Lead Candidate Consultant`)}
              name='leadCandidateConsultant'
              options={userOptions}
              placeholder={userPlaceholder}
            />
            <FormInputBlock
              type='percentage'
              label={i18n._(t`Lead Candidate Consultant Split`)}
              name='leadCandidateConsultantSplit'
            />
            <FormInputBlock
              type='select'
              label={i18n._(t`Support Consultant`)}
              name='supportConsultant'
              options={userOptions}
              placeholder={userPlaceholder}
            />
            <FormInputBlock
              type='percentage'
              label={i18n._(t`Support Consultant Split`)}
              name='supportConsultantSplit'
            />
            <FormInputBlock
              type='select'
              label={i18n._(t`Lead BD Consultant`)}
              name='leadBdConsultant'
              options={userOptions}
              placeholder={userPlaceholder}
            />
            <FormInputBlock
              type='percentage'
              label={i18n._(t`Lead BD Consultant Split`)}
              name='leadBdConsultantSplit'
            />
            <FormInputBlock
              type='select'
              label={i18n._(t`Client Originator`)}
              name='clientOriginator'
              options={userOptions}
              placeholder={userPlaceholder}
            />
            <FormInputBlock
              type='percentage'
              label={i18n._(t`Client Originator Split`)}
              name='clientOriginatorSplit'
            />
          </FormSection>

          <FormSection title={i18n._(t`Research Split Allocations`)}>
            <FormInputBlock
              type='select'
              label={i18n._(t`Activator`)}
              name='activator'
              options={userOptions}
              placeholder={userPlaceholder}
            />
            <FormInputBlock
              type='percentage'
              label={i18n._(t`Activator Split`)}
              name='activatorSplit'
            />
          </FormSection>
          {!(isDisabled && noFiles) ? (
            <FormSection title={i18n._(t`File`)}>
              <Col>
                <FormThumbnailList
                  name='files'
                  newFilesName='newFiles'
                  form={form}
                  setValue={setValue}
                  fetchOperationId='fee_split_allocation_get_file'
                  previewOperationId='fee_split_allocation_get_file'
                  deleteOperationId={
                    !isDisabled ? 'fee_split_allocation_delete_file' : null
                  }
                  onRemoved={handleFileRemoved}
                />
                {!isDisabled && noFiles ? (
                  <div className='file-input-wide'>
                    <FileInput
                      withoutNewFilesList
                      form={form}
                      setValue={setValue}
                      deleteOperationId='fee_split_allocation_delete_file'
                      filesKey='files'
                      newFilesKey='newFiles'
                      acceptedFileType='other'
                    />
                  </div>
                ) : null}
              </Col>
            </FormSection>
          ) : null}
        </div>
      )}
    />
  );
}

export default wrapper(FeeSplitAllocationFormContent);
