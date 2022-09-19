import React from 'react';

function FormHeader({ children }) {
  return (
    <div className='row align-items-center'>
      <div className='col'>{children}</div>
    </div>
  );
}

export default FormHeader;
