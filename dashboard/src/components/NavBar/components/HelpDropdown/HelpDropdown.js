import React, { memo } from 'react';
import { IoMdHelpCircle } from 'react-icons/all';

import { defineMessage } from '@lingui/macro';

import { openZendeskForm } from '@utils';
import { ActionsDropdown } from '@components';
import IconButton from '@components/UI/IconButton';

import styles from './HelpDropdown.module.scss';

const ACTIONS = [
  {
    transKey: defineMessage({ message: 'Contact Support' }).id,
    handler: openZendeskForm,
  },
  {
    transKey: defineMessage({ message: 'User Guide' }).id,
    link: 'https://zookeep.zendesk.com/hc',
  },
];

const HelpDropdown = () => {
  return (
    <div className={styles.container}>
      <ActionsDropdown
        actions={ACTIONS}
        button={
          <IconButton>
            <IoMdHelpCircle size={22} />
          </IconButton>
        }
      />
    </div>
  );
};

export default memo(HelpDropdown);
