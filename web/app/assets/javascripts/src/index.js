'use strict'

require('babel-polyfill')
var $ = require('jquery')

$(document).ready(function () {
  var app = require('./app.js')
  app.run()
})
