import { useMemo } from 'react';

import { translateMap } from '@utils';
import { GROUP_TO_ROLE_NAME_MAP } from '@constants';

export default function useGroupToRoleMap(i18n) {
  return useMemo(() => translateMap(i18n, GROUP_TO_ROLE_NAME_MAP), [i18n]);
}
