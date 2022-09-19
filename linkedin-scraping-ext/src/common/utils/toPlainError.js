export default (error) => ({
  name: error.name,
  message: error.message,
  response: error.response,
  fileName: error.fileName,
  columnNumber: error.columnNumber,
  lineNumber: error.lineNumber,
  stack: error.stack,
});
