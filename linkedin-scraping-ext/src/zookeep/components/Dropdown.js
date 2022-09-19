import DropdownItem from './DropdownItem';

const ALIGN = {
  left: 'left',
  right: 'right',
};

const defaultProps = {
  trigger: null,
  display: null,
  placeholder: 'Select',
  options: null,
  fetchOptions() {
    this.options = [];
  },
  onSelect: null,
  align: ALIGN.left,
};

export default class Dropdown {
  constructor(props) {
    const mergedProps = props ? { ...defaultProps, ...props } : defaultProps;

    const {
      trigger,
      placeholder,
      options,
      display,
      fetchOptions,
      onSelect,
      onChange,
      align,
    } = mergedProps;

    this.align = align;
    this.onSelect = onSelect;
    this.onChange = onChange;
    this._handleTrigger = this.handleTrigger.bind(this);
    this._handleClickOutside = this.handleClickOutside.bind(this);
    this._handleSelect = this.handleSelect.bind(this);
    this.placeholder = placeholder;

    const cls = this.constructor;
    this.trigger = trigger || cls.createTrigger();
    this.trigger.addEventListener('click', this._handleTrigger);

    this.display = display || this.createDisplay();
    this.anchor = this.trigger;

    this.menu = cls.createMenu();
    this.menu.style.visibility = 'hidden';
    document.body.appendChild(this.menu);

    this.list = cls.createList();
    this.menu.appendChild(this.list);

    this.value = null;
    this._isOpen = false;
    this._fetchOptions = fetchOptions.bind(this);
    if (options) {
      this.options = options;
    } else {
      this.options = [];
    }

    this.update();
  }

  static createTrigger() {
    const trigger = document.createElement('button');
    trigger.className = 'dropdownButton';
    return trigger;
  }

  static createList() {
    const list = document.createElement('div');
    list.className = 'dropdownContent__list';
    return list;
  }

  static createMenu() {
    const menu = document.createElement('div');
    menu.className = 'dropdownContent';
    return menu;
  }

  createDisplay() {
    const display = document.createElement('span');
    display.className = 'dropdownText';
    this.trigger.appendChild(display);
    return display;
  }

  handleTrigger() {
    this.isOpen = this.disabled ? false : !this.isOpen;
  }

  handleSelect(id) {
    if (this.onSelect) {
      this.onSelect(id);
    }
    this.value = id;
    this.isOpen = false;
  }

  handleClickOutside(event) {
    if (event.target === this.trigger || this.menu.contains(event.target)) return;
    this.isOpen = false;
  }

  updateText() {
    if (this._value) {
      const option = this.options.find((option) => option.id === this._value);
      this.display.innerText = option ? option.title : this.placeholder;
      return;
    }
    this.display.innerText = this.placeholder;
  }

  handleChange() {
    this.updateText();
    if (this.onChange) {
      this.onChange(this._value);
    }
  }

  removeAllButtons() {
    if (this.buttons) {
      this.buttons.forEach((button) => {
        button.remove();
      });
    }
  }

  updateButtons(options) {
    this.removeAllButtons();

    this.buttons = options.map(
      (option) => new DropdownItem(this.list, option, this._handleSelect)
    );
  }

  set options(options) {
    if (this._options !== options) {
      this.updateButtons(options);
      this._options = options;
      this.updateText();
    }
  }

  get options() {
    return this._options;
  }

  set disabled(value) {
    if (!value) {
      this.trigger.removeAttribute('disabled');
      return;
    }
    this.trigger.setAttribute('disabled', true);
  }

  get disabled() {
    return this.trigger.hasAttribute('disabled');
  }

  set value(val) {
    if (val !== this._value) {
      this._value = val;
      this.handleChange();
    }
  }

  get value() {
    return this._value;
  }

  get isOpen() {
    return this._isOpen;
  }

  set isOpen(value) {
    this._isOpen = value;
    this.update();
  }

  update() {
    if (this.isOpen) {
      document.body.addEventListener('click', this._handleClickOutside);
    } else {
      document.body.removeEventListener('click', this._handleClickOutside);
    }

    const box = this.anchor.getBoundingClientRect();
    const menuBox = this.menu.getBoundingClientRect();

    this.menu.style.visibility = this.isOpen ? 'visible' : 'hidden';

    this.menu.style.top = `${box.y + box.height + window.scrollY}px`;

    if (this.align === ALIGN.left) {
      this.menu.style.left = `${box.x + window.scrollX}px`;
    }

    if (this.align === ALIGN.right) {
      this.menu.style.left = `${box.x + box.width + window.scrollX - menuBox.width}px`;
    }
  }

  mount(triggerParent) {
    triggerParent.appendChild(this.trigger);
  }

  unmount() {
    this.trigger.remove();
  }
}
