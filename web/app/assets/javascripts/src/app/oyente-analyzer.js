'use strict'

var $ = require('jquery')

function getOptions () {
  var data = {}
  $('.oyente-opt').each( function () {
    var label = $(this).data('label')
    var val = $(this).find('input').val()
    if (val) {
      data[label] = val
    }
  })
  return data
}

function Analyzer () {

  this.analyze = function (source) {
    var data = getOptions()
    data['source'] = source

    $.ajax({
      type: 'POST',
      url: 'home/analyze',
      data: { 'data': data },
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
