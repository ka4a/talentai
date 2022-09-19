export default class DropdownItem {
  constructor(parent, option, onSelect) {
    this._handleClick = this.handleClick.bind(this);

    this.parent = parent;

    this.elem = document.createElement('button');
    this.elem.className = 'dropdownItem';

    this.id = option.id;
    this.title = option.title;

    this.parent.appendChild(this.elem);

    this._onSelect = onSelect;

    this.elem.addEventListener('click', this._handleClick);
  }

  handleClick() {
    this._onSelect(this.id);
  }

  set title(value) {
    this._title = value;
    this.elem.innerText = value;
  }

  get title() {
    return this._title;
  }

  remove() {
    this.elem.removeEventListener('click', this._handleClick);
    this.parent.removeChild(this.elem);
  }
}
