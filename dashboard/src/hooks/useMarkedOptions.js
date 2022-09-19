import { useMemo } from 'react';

import _ from 'lodash';

export default function useMarkedOptions(options, selected) {
  return useMemo(
    () =>
      _.map(options, (option) => ({
        ...option,
        isSelected: _.includes(selected, option.value),
      })),
    [options, selected]
  );
}
