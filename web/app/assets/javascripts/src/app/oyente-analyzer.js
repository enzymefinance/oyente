'use strict'

var $ = require('jquery')

function Analyzer () {
  this.analyze = function (source) {
    $.ajax({
      type: 'POST',
      url: 'http://localhost:3000/home/upload',
      data: { 'coding_file': source },
      dataType: 'json',
      success: function (response) {
        $('#analysis').empty()
        $('#analysis').append(response.result)
        $('#analysis').show()
      }
    })
  }
}

module.exports = Analyzer
