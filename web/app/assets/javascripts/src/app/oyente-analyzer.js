'use strict'

var $ = require('jquery')
var yo = require('yo-yo')

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
    $('#analyzer').html(loading)
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
        $('#analyzer').html(finish)

        $('#analysis').append(response.result)
        $('#analysis').fadeIn()
      }
    })
  }
}

module.exports = Analyzer
