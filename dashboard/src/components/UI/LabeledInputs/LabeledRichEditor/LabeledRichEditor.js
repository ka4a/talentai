import React, { memo, useCallback, useEffect, useMemo, useState } from 'react';

import PropTypes from 'prop-types';
import { createEditor } from 'slate';
import { Slate, Editable, withReact } from 'slate-react';
import { withHistory } from 'slate-history';
import isHotkey from 'is-hotkey';
import classnames from 'classnames';

import { Typography } from '@components';

import { serialize, deserialize } from './htmlConverter';
import Toolbar, { toggleMark } from './Toolbar';

import styles from './LabeledRichEditor.module.scss';

const HOTKEYS = {
  'mod+b': 'bold',
  'mod+i': 'italic',
  'mod+u': 'underline',
};

const defaultEditorValue = [
  {
    type: 'paragraph',
    children: [{ text: '' }],
  },
];

const LabeledRichEditor = (props) => {
  const {
    label,
    value,
    onChange,
    wrapperClassName,
    required,
    withoutCapitalize,
    ...rest
  } = props;
  const [editorValue, setEditorValue] = useState(defaultEditorValue);

  useEffect(() => {
    const document = new DOMParser().parseFromString(value, 'text/html');
    setEditorValue(value ? deserialize(document.body) : defaultEditorValue);
  }, [label, value]);

  const renderElement = useCallback((props) => <Element {...props} />, []);
  const renderLeaf = useCallback((props) => <Leaf {...props} />, []);

  const editor = useMemo(() => withHistory(withReact(createEditor())), []);

  const onKeyDown = useCallback(
    (event) => {
      for (const hotkey in HOTKEYS) {
        if (isHotkey(hotkey, event)) {
          event.preventDefault();
          const mark = HOTKEYS[hotkey];
          toggleMark(editor, mark);
        }
      }
    },
    [editor]
  );

  return (
    <Slate
      editor={editor}
      value={editorValue}
      onChange={(value) => {
        setEditorValue(value);
        onChange(serialize({ children: value }));
      }}
    >
      <div className={classnames([styles.wrapper, wrapperClassName])}>
        <div className={styles.innerWrapper}>
          <label
            className={classnames(styles.label, {
              [styles.withoutCapitalize]: withoutCapitalize,
            })}
          >
            <Typography variant='caption'>
              {label}
              {required && <span className={styles.required}>*</span>}
            </Typography>
          </label>

          <Editable
            className={styles.editor}
            renderElement={renderElement}
            renderLeaf={renderLeaf}
            onKeyDown={onKeyDown}
            {...rest}
          />

          <Toolbar />
        </div>
      </div>
    </Slate>
  );
};

const Leaf = ({ attributes, children, leaf }) => {
  if (leaf.bold) children = <strong>{children}</strong>;
  if (leaf.italic) children = <em>{children}</em>;
  if (leaf.underline) children = <u>{children}</u>;

  return <span {...attributes}>{children}</span>;
};

const Element = ({ attributes, children, element }) => {
  const tags = {
    'bulleted-list': 'ul',
    'list-item': 'li',
  };
  const Tag = tags[element.type] ?? 'p';
  return <Tag {...attributes}>{children}</Tag>;
};

LabeledRichEditor.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func,
  wrapperClassName: PropTypes.string,
  required: PropTypes.bool,
  withoutCapitalize: PropTypes.bool,
};

LabeledRichEditor.defaultProps = {
  label: '',
  value: '',
  wrapperClassName: '',
  required: false,
  withoutCapitalize: false,
  onChange: () => {},
};

export default memo(LabeledRichEditor);
