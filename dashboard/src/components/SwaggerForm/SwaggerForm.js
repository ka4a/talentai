import React from 'react';
import { Button, Form } from 'reactstrap';
import { withRouter } from 'react-router-dom';
import { toast } from 'react-toastify';

import PropTypes from 'prop-types';
import _ from 'lodash';
import { compose } from 'redux';
import { withI18n } from '@lingui/react';
import { Trans } from '@lingui/macro';

import { client } from '@client';
import {
  getErrorsInputFeedback,
  getErrorsInputInvalid,
  getErrorTextFromFetchError,
  saveChangeToStateObject,
  showErrorToast,
} from '@utils';
import BlockingPromptFormChanged from '@components/BlockingPromptFormChanged';
import FormHeader from '@components/UI/FormHeader';

import CustomFormInput from './CustomFormInput';
import ReqStatus from '../ReqStatus';

class SwaggerForm extends React.PureComponent {
  state = {
    saving: false,
    loading: false,
    // form might be hidden, but not loading, if an error occurred while fetch
    formVisible: false,
    form: {},
    cleanForm: {}, // compared with `form` to get changed fields
    errorMessage: null,
    errors: {},
    errorIds: [],
  };

  constructor(props) {
    super(props);

    if (this.props.editing && !this.props.readOperationId) {
      throw new Error('readOperationId is required when editing');
    }

    if (!this.props.editing && !this.props.initialState) {
      throw new Error('initialState is required when not editing');
    }

    this.state.form = _.cloneDeep(props.initialState);
    this.state.cleanForm = _.cloneDeep(props.initialState);

    this.state.formVisible = !props.editing;
    this.handlers = _.mapValues(props.handlers, (h) => h.bind(this));

    this.formRef = React.createRef();
  }

  fetchData = (id) => {
    this.setState({ loading: true }, () => {
      client
        .execute({
          operationId: this.props.readOperationId,
          parameters: { [this.props.lookupField]: id },
        })
        .then((response) => {
          const newFormState = {
            ..._.cloneDeep(this.props.initialState),
            ...(this.props.processReadObject !== null
              ? this.props.processReadObject(response.obj)
              : response.obj),
          };

          this.setState({
            loading: false,
            formVisible: true,
            form: newFormState,
            cleanForm: newFormState,
          });
        })
        .catch((error) => {
          this.setState({
            loading: false,
            formVisible: false,
            errorObj: error,
            errorMessage: getErrorTextFromFetchError(error),
          });
        });
    });
  };

  alertOnError = () => {
    showErrorToast(
      <Trans>Submission error: some fields are missing or improperly filled</Trans>,
      { autoClose: 5000 }
    );
  };

  handleSaveError = (error, errorStateKey) => {
    if (error?.response?.status === 400) {
      const errorData = error.response.obj;
      this.setState({
        errors: errorData,
        errorMessage: _.has(errorData, 'detail') ? errorData.detail : null,
        saving: false,
      });
      // if only nonFieldErrors, don't trigger generic alert
      if (_.isEmpty(_.omit(errorData, ['nonFieldErrors']))) return;
      this.alertOnError();
    }

    if (error?.message) {
      this.setState((prevState) => ({
        form: {
          ...prevState.form,
          [errorStateKey]: error.message,
        },
        saving: false,
      }));

      this.alertOnError();

      return;
    }

    this.setState({
      errors: {},
      errorObj: null,
      errorMessage: getErrorTextFromFetchError(error),
      saving: false,
    });
  };

  /*
   * Generic form submission handler
   * @param {object} event - button event
   * @param {object} data - additional data which would be added to form state during request
   * @param {object} resolveArgs - parameters which would be passed to onSaved handler
   * */
  onSubmit = async (event, data, resolveArgs) => {
    const {
      checkFormStateBeforeSave,
      processFormState,
      checkFieldsIdBeforeSave,
    } = this.props;
    event.preventDefault();

    this.cleanNonFieldErrors();

    if (this.formRef.current.reportValidity && !this.formRef.current.reportValidity()) {
      // this.formRef.current.reportValidity doesn't work in IE
      return;
    }

    const formState = this.state.form;
    let formData = { ...formState, ...data };

    if (processFormState) {
      formData = processFormState(formData);
    }

    if (checkFormStateBeforeSave) {
      this.setState({ saving: true });
      const isValid = await checkFormStateBeforeSave(
        formData,
        (patch) => Object.assign(formData, patch),
        (callback) => this.setState({ form: this.state.cleanForm }, callback),
        this.handleSaveError
      );
      if (!isValid) {
        this.setState({ saving: false });
        return;
      }
    }

    if (checkFieldsIdBeforeSave) {
      const updatedFormData = checkFieldsIdBeforeSave(formState);
      formData = { ...formState, ...updatedFormData };
    }

    this.setState({ saving: true }, () => {
      client
        .execute({
          operationId: this.props.operationId,
          parameters: {
            [this.props.lookupField]: formData.id,
            data: formData,
          },
        })
        .then((response) => {
          const newState = {
            form: formState,
            saving: false,
            errorMessage: null,
            errorObj: null,
            errors: {},
          };

          const { obj } = response;

          if (this.props.onFormSubmitDone) {
            this.props.onFormSubmitDone(
              (success, formPatch) =>
                this.finishSaveProcess(
                  { ...newState, form: { ...newState.form, ...formPatch } },
                  obj,
                  success,
                  resolveArgs
                ),
              obj,
              formState,
              this.setErrorMessage
            );
          } else {
            this.finishSaveProcess(newState, obj, true, resolveArgs);
          }
        })
        .catch(this.handleSaveError);
    });
  };

  setErrorMessage = (errorMessage) => {
    this.setState({ errorMessage });
  };

  /*
   * Returns form to initial state, fetches updated data and calls onSaved handler
   * @param {object} newState - new version of state after request
   * @param {object} obj - response data
   * @param {boolean} success - indicates if form submitted successfully
   * @param {object} resolveArgs - object passed from submit handler meant to affect logic of onSaved
   * */
  finishSaveProcess = (newState, obj, success = true, resolveArgs) => {
    let fetchDataAfterStateChanged = false;
    const { resetAfterSave, onSaved, editing, initialState } = this.props;
    const { form } = this.state;

    if (resetAfterSave) {
      if (typeof resetAfterSave === 'function') {
        newState.form = resetAfterSave(form, initialState, obj);
      } else {
        newState.form = initialState;
      }
      this.formRef.current.reset(); // To reset html5 validation

      if (editing) {
        newState.formVisible = false;
        fetchDataAfterStateChanged = true;
      }
    }

    if (success) {
      newState.cleanForm = newState.form;
    }

    this.setState(newState, () => {
      if (onSaved && success) {
        onSaved(obj, form, resolveArgs);
      }

      if (fetchDataAfterStateChanged) {
        this.fetchData(editing);
      }
    });
  };

  /*
   * Creates handler for form submission
   * @param {object} data - additional data which would be added to form state during request
   * @param {object} resolveArgs - parameters which would be passed to onSaved handler
   * */
  makeOnSubmit = (data, resolveArgs = {}) =>
    _.partial(this.onSubmit, _, data, resolveArgs);

  validateOnBlur = async (event) => {
    const {
      processValidationParams,
      validateOperationId,
      processFormState,
    } = this.props;
    const { form } = this.state;

    if (!validateOperationId) return;

    const formState = processFormState ? processFormState(form) : form;

    // for nested structures, it validates all nested values at once
    const path = _.toPath(event.target.name);
    const root = path[0];

    const defaultParams = { [root]: formState[root] };
    const partialFormState = processValidationParams
      ? processValidationParams(formState, path, defaultParams)
      : defaultParams;

    try {
      await client.execute({
        operationId: validateOperationId,
        parameters: {
          id: formState.id,
          data: partialFormState,
        },
      });

      this.setState((state) => ({
        errors: _.omit(state.errors, _.keys(partialFormState)),
      }));
    } catch (error) {
      if (error?.response?.status === 400) {
        this.setState((state) => ({
          errors: {
            ...state.errors,
            ..._.pick(error.response.obj, _.keys(partialFormState)),
          },
        }));
      }
    }
  };

  onChange = saveChangeToStateObject().bind(this);

  setValue = (path, value) => {
    this.setState((state) => {
      const formState = { ...state.form };
      _.set(formState, path, value);
      return { form: formState };
    });
  };

  componentDidMount() {
    if (this.props.editing) {
      this.fetchData(this.props.editing);
    }
  }

  componentDidUpdate(prevProps, { errorMessage: oldErrorMessage }, snapshot) {
    const { errorMessage, errorObj } = this.state;
    if (
      oldErrorMessage !== errorMessage &&
      typeof errorMessage === 'string' &&
      _.get(errorObj, 'statusCode') !== 404
    ) {
      showErrorToast(errorMessage);
    }
  }

  FormInput = ({
    name,
    type,
    label = null,
    renderErrors = true,
    options,
    disabled,
    nameForError,
    ...rest
  }) => (
    <div className='d-flex flex-column'>
      <CustomFormInput
        id={`${this.props.formId}_${name}`}
        type={type}
        name={name}
        label={label}
        invalid={getErrorsInputInvalid(this.state.errors, name)}
        options={options}
        value={_.get(this.state.form, name)}
        setValue={this.setValue}
        errors={this.state.errors}
        validate={this.validateOnBlur}
        onChange={this.onChange}
        disabled={disabled || this.isDisabled()}
        {...rest}
      />

      {renderErrors && getErrorsInputFeedback(this.state.errors, nameForError ?? name)}
    </div>
  );

  FormInputBlock = ({ xs, md, lg, isWide, containerTooltip, ...rest }) => {
    const { FormInput } = this;
    // const xsDefault = 12;
    // let mdDefault = xs || isWide ? null : 6;

    return (
      // <Col title={containerTooltip} xs={xs || xsDefault} md={md || mdDefault}>
      // <FormGroup>
      <FormInput {...rest} />
      // </FormGroup>
      // </Col>
    );
  };

  onFormSubmit = (event) => {
    event.preventDefault();
    this.onSubmit(event, this.props.defaultSubmitData);
  };

  renderButtons({ atBottom = true } = {}) {
    const { buttons } = this.props;
    const { saving, loading, formVisible, form } = this.state;

    const defaultButtonAttrs = { disabled: saving };

    if (loading || !formVisible) return null;

    if (!buttons) {
      return (
        <div>
          <Button {...defaultButtonAttrs}>Save</Button>
        </div>
      );
    } else {
      return buttons(form, this.makeOnSubmit, defaultButtonAttrs, atBottom);
    }
  }

  isDisabled() {
    const { isDisabled } = this.props;

    return typeof isDisabled === 'function' ? isDisabled(this.state.form) : isDisabled;
  }

  handleNonFieldErrors = (errors) => {
    const errorIds = [];
    _.forEach(errors, (e) => {
      const errorId = _.uniqueId('error_');
      errorIds.push(errorId);
      showErrorToast(e, {
        toastId: errorId,
        onClose: () =>
          this.setState({
            errorIds: _.filter(this.state.errorIds, (id) => id !== errorId),
          }),
      });
    });
    this.setState({ errorIds, errors: [] });
  };

  cleanNonFieldErrors = () => {
    const { errorIds } = this.state;
    _.forEach(errorIds, (id) => toast.dismiss(id));
    this.setState({ errorIds: [] });
  };

  componentWillUnmount() {
    this.cleanNonFieldErrors();
  }

  render() {
    const { handlers } = this;
    const { inputs, formTop } = this.props;
    const { loading, formVisible, form, errors, errorObj, cleanForm } = this.state;

    return (
      <Form onSubmit={this.onFormSubmit} innerRef={this.formRef}>
        {(loading || errorObj) && <ReqStatus {...{ loading, error: errorObj }} />}

        {formVisible && (
          <>
            <FormHeader>
              <BlockingPromptFormChanged initialForm={cleanForm} form={form} />

              {formTop && <div className='d-flex'>{formTop(form)}</div>}
            </FormHeader>

            {inputs({
              form,
              errors,
              handlers,
              onChange: this.onChange,
              setValue: this.setValue,
              FormLabel: this.FormLabel,
              FormInput: this.FormInput,
              FormInputBlock: this.FormInputBlock,
              isDisabled: this.isDisabled(),
            })}

            {_.has(errors, 'nonFieldErrors') &&
              this.handleNonFieldErrors(errors.nonFieldErrors)}
          </>
        )}

        {this.renderButtons()}
      </Form>
    );
  }
}

SwaggerForm.propTypes = {
  formId: PropTypes.string.isRequired,

  readOperationId: PropTypes.string,
  operationId: PropTypes.string.isRequired,
  validateOperationId: PropTypes.string,
  isDisabled: PropTypes.oneOfType([PropTypes.bool, PropTypes.func]),

  processReadObject: PropTypes.func,
  processFormState: PropTypes.func,
  processValidationParams: PropTypes.func,
  onFormSubmitDone: PropTypes.func,
  checkFormStateBeforeSave: PropTypes.func,
  checkFieldsIdBeforeSave: PropTypes.func,

  editing: PropTypes.any,
  onSaved: PropTypes.func,

  handlers: PropTypes.object,

  defaultSubmitData: PropTypes.object,

  initialState: PropTypes.object,
  formTop: PropTypes.func,
  inputs: PropTypes.func.isRequired,
  buttons: PropTypes.func,

  resetAfterSave: PropTypes.oneOfType([
    PropTypes.func.isRequired, // (form, initialState, responseObj) => newForm
    PropTypes.bool.isRequired,
  ]),
  lookupField: PropTypes.string,
};

SwaggerForm.defaultProps = {
  processReadObject: null,
  processFormState: null,
  onFormSubmitDone: null,

  editing: false,
  handlers: {},
  defaultSubmitData: {},
  buttons: null,
  resetAfterSave: false,
  lookupField: 'id',
};

export default compose(withI18n(), withRouter)(SwaggerForm);
