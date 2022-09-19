import React, { useRef } from 'react';

import MenuPortalContext from './MenuPortalContext';

import styles from './LabeledMultiSelect.module.scss';

function LabeledMultiSelectMenuPortalProvider({ children }) {
  const menuContainerRef = useRef(null);

  return (
    <>
      <MenuPortalContext.Provider value={menuContainerRef}>
        {children}
      </MenuPortalContext.Provider>
      <div className={styles.menu} ref={menuContainerRef} />
    </>
  );
}

export default LabeledMultiSelectMenuPortalProvider;
