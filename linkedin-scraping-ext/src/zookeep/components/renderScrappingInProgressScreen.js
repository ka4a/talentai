export default () => `
  <div id="ext-block-screen" style="
    position: fixed;
    background-color: rgba(0,0,0,0.9);
    bottom: 0;
    top: 0;
    left: 0;
    right: 0;
    z-index: 16777271;"
  >
    <div style="
      display: flex;
      justify-content: center;
      align-items: center;
      width: 100%;
      height: 100%;
    ">
      <div style="
        color: white;
        font-size: 32pt;
      ">
        Loading data...<br/>Please do not switch tabs
      </div>
    </div>
  </div>
`;
