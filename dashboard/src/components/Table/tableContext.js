import React from 'react';

const TableContext = React.createContext({
  isOpenColumn: false,
  withBorder: true,
  storeKey: '',
});

export default TableContext;
