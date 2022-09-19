import React, { memo } from 'react';

import PropTypes from 'prop-types';
import _ from 'lodash';

import LocalPropTypes from './LocalPropTypes';

function AgencyCategories(props) {
  const { agency, categoryGroups, categories, functionFocus } = props;

  const agencyCategoriesPerGroup = _.chain(categories)
    .filter((c) => _.includes(agency.categories, c.id))
    .groupBy('group')
    .value();

  const agencyFunctionFocus = _.filter(functionFocus, ({ id }) =>
    _.includes(agency.functionFocus, id)
  );

  return (
    <>
      {agencyFunctionFocus.length ? (
        <div className='mt-24'>
          <div className='text-uppercase font-weight-bold'>Function Focus</div>
          {_.map(agencyFunctionFocus, (c) => (
            <div key={c.id}>{c.title}</div>
          ))}
        </div>
      ) : null}

      {_.map(categoryGroups, (g) => {
        const currentCategories = agencyCategoriesPerGroup[g];

        if (!currentCategories || !currentCategories.length) {
          return null;
        }

        return (
          <div key={g} className='mt-24'>
            <div className='text-uppercase font-weight-bold'>{g}</div>
            {_.map(currentCategories, (c) => (
              <div key={c.id}>{c.title}</div>
            ))}
          </div>
        );
      })}
    </>
  );
}

AgencyCategories.propTypes = {
  agency: PropTypes.shape({
    functionFocus: PropTypes.arrayOf(PropTypes.number),
  }),
  categoryGroups: LocalPropTypes.categoryGroups,
  categories: LocalPropTypes.arrayOfOptions,
  functionFocus: LocalPropTypes.arrayOfOptions,
};

AgencyCategories.defaultProps = {
  agency: [],
  categoryGroups: [],
  categories: [],
  functionFocus: [],
};

export default memo(AgencyCategories);
