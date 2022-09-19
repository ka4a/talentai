const createReducer = (initialState, actionHandlerMap) => (
  state = initialState,
  { type, payload }
) => {
  const actionHandler = actionHandlerMap[type];
  return actionHandler ? actionHandler(state, payload) : state;
};

export default createReducer;
