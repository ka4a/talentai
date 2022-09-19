import debounce from 'lodash/debounce';
import Dropdown from './Dropdown';
import { ICON_CHEVRON_DOWN_HTML, ICON_SEARCH_HTML } from '../icons';

export default class ButtonMenu extends Dropdown {
  constructor(props) {
    super(props);

    this._handleSearchChange = debounce(this.fetchOptionsWithFilter.bind(this), 500);

    this.searchInput = document.createElement('input');
    this.searchInput.className = 'searchInput';
    this.searchInput.placeholder = 'Search job';
    this.searchInput.addEventListener('input', this._handleSearchChange);

    const searchInputContainer = document.createElement('div');
    searchInputContainer.className = 'searchInputContainer';
    // search icon
    searchInputContainer.innerHTML = ICON_SEARCH_HTML;
    searchInputContainer.appendChild(this.searchInput);

    this.menu.insertBefore(searchInputContainer, this.list);
    this._filter = '';
    this._fetchAfterLastChangeTimerID = null;
  }

  get filter() {
    return this._filter;
  }

  set filter(value) {
    this._filter = value;
    this.searchInput.value = value;
  }

  fetchOptionsWithFilter() {
    this._fetchOptions(this.searchInput.value);
  }

  handleSearchChange() {
    debounce(this._fetchOptionsWithFilter, this.fetchDelay);
  }

  createDisplay() {
    const display = document.createElement('div');
    display.className = 'zookeep__button_add__subtitle';
    return display;
  }

  static createTrigger() {
    const trigger = document.createElement('button');
    trigger.className = 'zookeep__button zookeep__button_menuButton';
    trigger.innerHTML = ICON_CHEVRON_DOWN_HTML;
    return trigger;
  }

  update() {
    super.update();
    if (this.menu && this.anchor && this.trigger) {
      const anchor = this.anchor.getBoundingClientRect();
      const trigger = this.trigger.getBoundingClientRect();
      const width = anchor.width + trigger.width;
      this.menu.style.width = width + 'px';
    }
  }

  mount(anchor) {
    anchor.parentNode.insertBefore(this.trigger, anchor.nextSibling);
    this.anchor = anchor;
    anchor.appendChild(this.display);
  }

  unmount() {
    super.unmount();
    this.display.remove();
  }
}
