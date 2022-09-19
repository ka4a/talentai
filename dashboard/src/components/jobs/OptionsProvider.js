import { memo, cloneElement, useState, useEffect } from 'react';

import PropTypes from 'prop-types';
import _ from 'lodash';

import { fetchErrorHandler } from '@utils';
import { client } from '@client';

const propTypes = {
  children: PropTypes.node,
  operationId: PropTypes.string.isRequired,
  parameters: PropTypes.object,
  getValue: PropTypes.func.isRequired,
  getLabel: PropTypes.func.isRequired,
  filterPredicate: PropTypes.func,
};

const defaultProps = {
  filterPredicate: () => true,
};

const OptionsProvider = ({
  children,
  operationId,
  parameters,
  getValue,
  getLabel,
  filterPredicate,
}) => {
  const [options, setOptions] = useState([]);

  useEffect(() => {
    client
      .execute({
        operationId,
        parameters,
      })
      .then((data) => {
        const results = _.get(data, 'obj.results', []);
        const options = _.chain(results)
          .filter(filterPredicate)
          .map((obj) => ({
            value: getValue(obj),
            label: getLabel(obj),
          }))
          .value();

        setOptions(options);
      })
      .catch(fetchErrorHandler);
  }, [getLabel, getValue, parameters, operationId, filterPredicate]);

  return cloneElement(children, { options });
};

OptionsProvider.propTypes = propTypes;
OptionsProvider.defaultProps = defaultProps;

export default memo(OptionsProvider);
