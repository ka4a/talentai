import React, { memo, useCallback, useState } from 'react';
import { TabContent, TabPane, Nav, NavLink } from 'reactstrap';

import PropTypes from 'prop-types';
import classnames from 'classnames';

import Typography from '../Typography';

import styles from './Tabs.module.scss';

const Tabs = ({ tabs, activeTabId, onChangeTab, className }) => {
  const [activeTab, setActiveTab] = useState(activeTabId || 1);

  const handleChangeTab = useCallback(
    (tab) => {
      if (activeTab !== tab) setActiveTab(tab);
      if (onChangeTab) onChangeTab(tab);
    },
    [activeTab, onChangeTab]
  );

  return (
    <div className={styles.wrapper}>
      <div className={classnames(['tabs', styles.tabs, className])}>
        <Nav tabs>
          {tabs.map((tab) => (
            <NavLink
              key={`tab-${tab.id}`}
              className={classnames({
                active: activeTab === tab.id,
                [styles.disabled]: tab.isDisabled,
              })}
              onClick={() => {
                handleChangeTab(tab.id);
              }}
            >
              <Typography>{tab.title}</Typography>
            </NavLink>
          ))}
        </Nav>
      </div>

      <TabContent activeTab={activeTab}>
        {tabs?.map((tab) => (
          <TabPane tabId={tab.id} key={`tabContent-${tab.id}`}>
            {tab.component}
          </TabPane>
        ))}
      </TabContent>
    </div>
  );
};

Tabs.propTypes = {
  title: PropTypes.string,
  activeTabId: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
  onChangeTab: PropTypes.func,
  tabs: PropTypes.arrayOf(
    PropTypes.shape({
      title: PropTypes.string,
      isDisabled: PropTypes.bool,
      id: PropTypes.number,
      component: PropTypes.element,
    })
  ),
  className: PropTypes.string,
};

Tabs.defaultProps = {
  tabs: [],
  className: '',
};

export default memo(Tabs);
