'use strict'

var $ = require('jquery')
var yo = require('yo-yo')

function getOptions () {
  var data = {}
  $('#oyente-options input').each( function () {
    var attr = $(this).attr('name')
    var val = $(this).val()
    if (val) {
      data[attr] = val
    }
  })
  return data
}

function Analyzer () {

  this.analyze = function (filename, source) {
    var data = getOptions()
    data['source'] = source
    data['filename'] = filename

    var loading = yo`
      <span>
        <i class="fa fa-cog fa-spin fa-fw">  </i>
        Analyzing ...
      </span>
    `
    $('#analyzer').html(loading).css('pointer-events', 'none')
    $('#analysis').empty().hide()

    $.ajax({
      type: 'POST',
      url: 'home/analyze',
      data: { 'data': data },
      dataType: 'json',
      success: function (response) {
        var finish = yo`
          <span>
            <i class="fa fa-search" aria-hidden="true">  </i>
            Analyze
          </span>
        `
        $('#analysis').append(response.result)
        $('#analyzer').html(finish).css('pointer-events', 'auto')
        $('#analysis').fadeIn()
      }
    })
  }
}

module.exports = Analyzer
