import { memo, cloneElement, useState, useEffect } from 'react';

import PropTypes from 'prop-types';
import _ from 'lodash';

import { fetchErrorHandler } from '@utils';
import { client } from '@client';

const UserOptionsProvider = ({ children, render }) => {
  const [options, setOptions] = useState([]);

  useEffect(() => {
    client
      .execute({ operationId: 'staff_list' })
      .then((data) =>
        setOptions(
          _.map(_.get(data, 'obj.results', []), (user) => ({
            value: user.id,
            label: `${user.firstName} ${user.lastName}`,
          }))
        )
      )
      .catch(fetchErrorHandler);
  }, []);

  if (render) return render(options);

  return cloneElement(children, { options });
};

UserOptionsProvider.propTypes = {
  children: PropTypes.node,
  render: PropTypes.func,
};

export default memo(UserOptionsProvider);
