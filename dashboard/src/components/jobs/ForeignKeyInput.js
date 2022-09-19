import React from 'react';
import { Alert, FormGroup, Input, Label, ListGroup, ListGroupItem } from 'reactstrap';

import PropTypes from 'prop-types';
import _ from 'lodash';

import { client } from '@client';

import { Loading } from '../UI/Loading';

export default class ForeignKeyInput extends React.Component {
  state = {
    searchText: '',
    options: null,
    loading: true,
  };

  fetchOptions(searchText) {
    client
      .execute({
        operationId: this.props.operationId,
        parameters: {
          ...this.props.params,
          /* TODO: maybe add pagination if only 5 results will be a problem */
          limit: 5,
          search: searchText,
        },
      })
      .then((response) => {
        // TODO: maybe add debounce instead:
        if (!searchText || this.state.searchText === searchText) {
          this.setState({
            options: response.obj.results,
            loading: false,
          });
        }
      }); // TODO: propagate error to form?
  }

  componentDidMount() {
    this.fetchOptions(null);
  }

  getUnselectedOptions = () =>
    _.filter(this.state.options, (el) => el.id !== this.props.value);

  onSearchTextChange = (event) => {
    this.setState({ searchText: event.target.value }, () => {
      this.fetchOptions(this.state.searchText);
    });
  };

  render() {
    const {
      title,
      value,
      errors,
      getOptionNameFn,
      getOptionSelectedNameFn,
    } = this.props;
    const { searchText, loading } = this.state;

    if (loading) {
      return <Loading />;
    }

    return (
      <FormGroup>
        <Label>{title}</Label>

        <FormGroup>
          <Label>
            <strong>
              {getOptionSelectedNameFn
                ? getOptionSelectedNameFn(value)
                : getOptionNameFn(value)}
            </strong>
          </Label>
        </FormGroup>

        {errors
          ? errors.map((error, i) => (
              <Alert key={i} color='danger'>
                {error}
              </Alert>
            ))
          : null}

        <Input
          className='my-4'
          name='searchText'
          placeholder={`Search ${title}...`}
          value={searchText}
          onChange={this.onSearchTextChange}
        />

        <ListGroup>
          {this.getUnselectedOptions().map((option) => (
            <ListGroupItem
              key={option.id}
              tag='button'
              type='button'
              action
              onClick={() => this.props.onChange(option)}
            >
              {getOptionNameFn(option)}
            </ListGroupItem>
          ))}
        </ListGroup>
      </FormGroup>
    );
  }
}

ForeignKeyInput.propTypes = {
  title: PropTypes.string.isRequired,
  operationId: PropTypes.string.isRequired,
  params: PropTypes.object,
  getOptionNameFn: PropTypes.func,
  getOptionSelectedNameFn: PropTypes.func,
  value: PropTypes.any.isRequired,
  onChange: PropTypes.func.isRequired,
  errors: PropTypes.array,
};

ForeignKeyInput.defaultProps = {
  getOptionNameFn: (option) => option.name,
};
