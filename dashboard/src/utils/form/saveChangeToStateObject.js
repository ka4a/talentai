import _ from 'lodash';

function saveChangeToStateObject(objName = 'form', setStateHandler) {
  return function (event) {
    const target = event.target;

    const path = target.name;

    let value;
    if (target.type === 'checkbox') {
      value = target.checked;
    } else if (target.type === 'select-multiple') {
      value = _.map(target.selectedOptions, 'value');
    } else {
      value = target.value;
    }

    const formState = { ...this.state[objName] };
    _.set(formState, path, value);

    this.setState(
      { [objName]: formState },
      setStateHandler ? () => setStateHandler(path) : undefined
    );
  };
}

export default saveChangeToStateObject;
