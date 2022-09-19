import { memo } from 'react';
import ReactDOM from 'react-dom';

function Portal({ children, target = document.body }) {
  return ReactDOM.createPortal(children, target);
}

export default memo(Portal);
