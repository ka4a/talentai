const webpack = require('webpack');
const path = require('path');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const ChromeExtensionReloader = require('webpack-chrome-extension-reloader');

module.exports = {
  mode: process.env.NODE_ENV || 'development',
  devtool: 'inline-source-map',
  entry: {
    main: path.join(__dirname, 'main.js'),
    background: path.join(__dirname, 'background.js'),
    popup: path.join(__dirname, 'popup.js'),
  },
  output: {
    path: path.join(__dirname, 'build'),
    filename: '[name].bundle.js',
  },
  module: {
    rules: [],
  },
  plugins: [
    new CleanWebpackPlugin(['build']),
    new webpack.EnvironmentPlugin(['NODE_ENV']),
    new CopyWebpackPlugin([
      {
        from: 'src/hccr/public/manifest.json',
      },
      {
        from: 'src/hccr/public/img/',
        to: 'img/',
      },
      {
        from: 'src/hccr/public/css/',
        to: 'css/',
      },
      {
        from: 'node_modules/bootstrap/dist/css/bootstrap.min.css',
        to: 'css/',
      },
      {
        from: 'src/hccr/public/*.html',
        flatten: true,
      },
    ]),
    new ChromeExtensionReloader(),
  ],
};
