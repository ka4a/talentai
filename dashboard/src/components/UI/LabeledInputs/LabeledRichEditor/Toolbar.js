import React, { memo, useMemo } from 'react';
import {
  AiOutlineBold,
  AiOutlineItalic,
  AiOutlineUnderline,
  AiOutlineUnorderedList,
} from 'react-icons/ai';

import classnames from 'classnames';
import PropTypes from 'prop-types';
// import { HiOutlineMenuAlt2, HiOutlineMenuAlt3, HiOutlineMenu } from 'react-icons/hi';
import { Editor, Element as SlateElement, Transforms } from 'slate';
import { useSlate } from 'slate-react';

import styles from '@components/UI/LabeledInputs/LabeledRichEditor/LabeledRichEditor.module.scss';

const ICONS = {
  bold: AiOutlineBold,
  italic: AiOutlineItalic,
  underline: AiOutlineUnderline,
  'bulleted-list': AiOutlineUnorderedList,
};
const LIST_TYPES = ['bulleted-list'];

//TODO: Add align functionality to currently commented buttons to slate editor in 1.1.0 version

const Toolbar = () => (
  <div className={styles.toolbar}>
    <div className={styles.toolbarSection}>
      <MarkButton format='bold' />
      <MarkButton format='italic' />
      <MarkButton format='underline' />
      <MarkButton format='bulleted-list' isBlock />
    </div>
    {/* <div className={styles.toolbarSection}>
      <div className={styles.markButton}>
        <HiOutlineMenuAlt2 />
      </div>
      <div className={styles.markButton}>
        <HiOutlineMenu />
      </div>
      <div className={styles.markButton}>
        <HiOutlineMenuAlt3 />
      </div>
    </div> */}
  </div>
);

const MarkButton = ({ format, isBlock }) => {
  const editor = useSlate();

  const Icon = useMemo(() => ICONS[format], [format]);

  const isActive = isBlock ? isBlockActive : isMarkActive;
  const toggle = isBlock ? toggleBlock : toggleMark;

  return (
    <div
      className={classnames([
        styles.markButton,
        { [styles.isActive]: isActive(editor, format) },
      ])}
      onMouseDown={(event) => {
        event.preventDefault();
        toggle(editor, format);
      }}
    >
      <Icon />
    </div>
  );
};

const isBlockActive = (editor, format) => {
  const [match] = Editor.nodes(editor, {
    match: (n) => !Editor.isEditor(n) && SlateElement.isElement(n) && n.type === format,
  });
  return !!match;
};

const isMarkActive = (editor, format) => {
  const marks = Editor.marks(editor);
  return marks ? marks[format] === true : false;
};

const toggleBlock = (editor, format) => {
  const isActive = isBlockActive(editor, format);
  const isList = LIST_TYPES.includes(format);

  Transforms.unwrapNodes(editor, {
    match: (n) =>
      LIST_TYPES.includes(!Editor.isEditor(n) && SlateElement.isElement(n) && n.type),
    split: true,
  });

  const listType = isList ? 'list-item' : format;
  const type = isActive ? 'paragraph' : listType;
  Transforms.setNodes(editor, { type });

  if (!isActive && isList) {
    const block = { type: format, children: [] };
    Transforms.wrapNodes(editor, block);
  }
};

export const toggleMark = (editor, format) => {
  const isActive = isMarkActive(editor, format);

  if (isActive) Editor.removeMark(editor, format);
  else Editor.addMark(editor, format, true);
};

MarkButton.propTypes = {
  format: PropTypes.string.isRequired,
  isBlock: PropTypes.bool,
};

MarkButton.defaultProps = {
  isBlock: false,
};

export default memo(Toolbar);
