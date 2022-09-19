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
    dashboard: path.join(__dirname, 'dashboard.js'),
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
        from: 'src/zookeep/manifest.json',
        transform: function (content, path) {
          // generates the manifest file using the package.json information

          const manifest = JSON.parse(content.toString());

          if (process.env.NODE_ENV === 'development') {
            manifest.permissions.push('http://localhost:3000/*');
            manifest['content_scripts'].push({
              matches: ['*://localhost/*'],
              js: ['dashboard.bundle.js'],
            });
          } else {
            manifest['content_scripts'].push({
              matches: ['https://zookeep.com/*'],
              js: ['dashboard.bundle.js'],
            });
          }

          return Buffer.from(
            JSON.stringify({
              ...manifest,
              version: process.env.npm_package_version,
            })
          );
        },
      },
      {
        from: 'src/zookeep/img/',
        to: 'img/',
      },
      {
        from: 'src/zookeep/css/',
        to: 'css/',
      },
    ]),
    new ChromeExtensionReloader(),
  ],
};
