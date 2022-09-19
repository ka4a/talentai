import ButtonMenu from './ButtonMenu';
import Dropdown from './Dropdown';
import toProposalPresetStr from '../../common/utils/toProposalPresetStr';
import { ICON_CHEVRON_DOWN_HTML } from '../icons';
import { btnText } from '../const';

import wrapInDiv from '../../common/dom/wrapInDiv';
import wrapTextInDiv from '../../common/dom/wrapTextInDiv';

function wrapSelector(title, selector) {
  return wrapInDiv('floatingPanel__select-container', [
    wrapTextInDiv('floatingPanel__select-label', title),
    selector.trigger,
  ]);
}

function addClass(elem, className) {
  elem.className = `${elem.className} ${className}`;
  return elem;
}

function addIcon(parent, iconHtml) {
  const container = document.createElement('svg');
  parent.appendChild(container);
  container.outerHTML = iconHtml;
}

export default class FloatingPanel {
  constructor({ onSelect, fetchOptions }) {
    this._handleSelectJob = this.handleSelectJob.bind(this);
    this._handleSelectStage = this.handleSelectStage.bind(this);
    this._onSelect = onSelect;

    this.stageMenu = new Dropdown({
      onSelect: this._handleSelectStage,
      align: 'right',
      placeholder: 'None',
      options: [
        { id: 'longlist', title: 'Longlist' },
        { id: 'shortlist', title: 'Shortlist' },
      ],
    });
    this.jobMenu = new ButtonMenu({
      fetchOptions,
      onSelect: this._handleSelectJob,
      align: 'right',
      placeholder: btnText.candidatesDB,
      onChange: (job) => {
        const noJob = job == null;
        this.stageMenu.disabled = noJob;
        this.stageMenu.value = noJob ? null : this.stageMenu.value || 'longlist';
      },
    });

    addIcon(this.stageMenu.trigger, ICON_CHEVRON_DOWN_HTML);
    this.stageMenu.trigger.className = 'floatingPanel__select-button';
    this.stageMenu.display.className = 'floatingPanel__select-button-content';

    this.jobMenu.anchor = this.jobMenu.trigger;
    this.jobMenu.trigger.insertBefore(
      this.jobMenu.display,
      this.jobMenu.trigger.children[0]
    );
    this.jobMenu.trigger.className = 'floatingPanel__select-button';
    this.jobMenu.display.className = 'floatingPanel__select-button-content';

    addClass(this.jobMenu.menu, 'floatingPanel__menu');
    addClass(this.stageMenu.menu, 'floatingPanel__menu floatingPanel__menu_short');

    this.element = wrapInDiv('floatingPanel', [
      wrapTextInDiv('floatingPanel__title', 'ZooKeep.io Extension'),
      wrapInDiv('floatingPanel__content', [
        wrapSelector('Job', this.jobMenu),
        wrapSelector('List', this.stageMenu),
      ]),
    ]);
    this.visible = false;

    this._onSelect = onSelect;
  }

  set visible(val) {
    this.element.style.visibility = val ? 'visible' : 'hidden';
  }

  get visible() {
    return this.element != null && !(this.element.style.visibility === 'hidden');
  }

  getPreset(preset) {
    const { job, stage } = preset ? JSON.parse(preset) : {};
    this.jobMenu.value = job;
    this.stageMenu.value = stage;
  }

  handleSelect(job, stage) {
    if (!this._onSelect) return;
    this._onSelect(toProposalPresetStr(job, stage));
  }

  handleSelectJob(job) {
    if (!job) {
      this._onSelect(null);
      return;
    }
    this.handleSelect(job, this.stageMenu.value || 'longlist');
  }
  handleSelectStage(stage) {
    this.handleSelect(this.jobMenu.value, stage);
  }

  mount(elem) {
    elem.appendChild(this.element);
  }
}
