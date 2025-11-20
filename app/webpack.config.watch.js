const base = require('./webpack.config');
//const ExtraWatchWebpackPlugin = require('extra-watch-webpack-plugin');

module.exports = [
  {
    ...base[0],
    bail: false,
    watch: true,
    plugins: [...base[0].plugins]
  },
  ...base.slice(1)
];
