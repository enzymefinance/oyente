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

  var loading_effect = function () {
    var loading = yo`
      <span>
        <i class="fa fa-cog fa-spin fa-fw">  </i>
        Analyzing ...
      </span>
    `
    $('#analyzer').html(loading).css('pointer-events', 'none')
    $('#analysis').empty().hide()
  }

  var finish_effect = function (results) {
    var finish = yo`
      <span>
        <i class="fa fa-search" aria-hidden="true">  </i>
        Analyze
      </span>
    `
    $('#analysis').append(results)
    $('#analyzer').html(finish).css('pointer-events', 'auto')
    $('#analysis').fadeIn()
  }

  var bug_exists = function(msg) {
    if (msg) {
      return $.parseHTML("<span style='color: red'>True</span>")
    } else{
      return $.parseHTML("<span style='color: green'>False</span>")
    }
  }

  this.analyze_bytecode = function (bytecode) {
    loading_effect()
    var data = getOptions()
    data['bytecode'] = bytecode

    $.ajax({
      type: 'POST',
      url: 'home/analyze_bytecode',
      data: { 'data': data },
      dataType: 'json',
      error: function(jqXHR, exception) {
        var error = yo`<div>
          Some errors occured. Please try again!
        </div>`
        finish_effect(error)
      },
      success: function (response) {
        var data = response.result
        if (data.hasOwnProperty("error")) {
          var error = yo`<div>
            <div>Bytecode analysis</div>
            <br />
            <div>${data.error}</div>
          </div>`
          finish_effect(error)
        }
        else {
          var res = data.result
          var result = yo`<div>
            <div style="font-weight: bold">Bytecode analysis</div>
            <br />
            <div>EVM code coverage: ${res.evm_code_coverage}%</div>
            <div>Callstack bug: ${bug_exists(res.callstack)}</div>
            <div>Money concurrency bug: ${bug_exists(res.money_concurrency)}</div>
            <div>Timedependency bug: ${bug_exists(res.time_dependency)}</div>
            <div>Reentrancy bug: ${bug_exists(res.reentrancy)}</div>
          </div>`
          finish_effect(result)
        }
      }
    })
  }

  this.analyze = function (current_file, sources) {
    loading_effect()

    var data = getOptions()
    data['sources'] = JSON.stringify(sources)
    data['current_file'] = current_file

    $.ajax({
      type: 'POST',
      url: 'home/analyze',
      data: { 'data': data },
      dataType: 'json',
      error: function(jqXHR, exception) {
        var error = yo`<div>
          Some errors occured. Please try again!
        </div>`
        finish_effect(error)
      },
      success: function (response) {
        var data = response.results
        var filename = data.filename

        if (data.hasOwnProperty("error")) {
          var results = yo`<div>
            <div>${filename}</div>
            <br />
            <div>${data.error}</div>
          </div>`
        } else {
          var contracts = data.contracts
          var results = yo`<div>
            ${Object.keys(contracts).map(function(filename) {
              return yo`<div>
                <div style="font-weight: bold">${filename}</div>
                <br />
                ${contracts[filename].map(function (contract) {
                  if (contract.evm_code_coverage === "0/0") {
                    return yo`<div>
                      <div>======= contract ${contract.cname} =======</div>
                      <div>EVM code coverage: ${contract.evm_code_coverage}</div>
                      <div>Callstack bug: ${bug_exists(contract.callstack)}</div>
                      <div>Money concurrency bug: ${bug_exists(contract.money_concurrency)}</div>
                      <div>Time dependency bug: ${bug_exists(contract.time_dependency)}</div>
                      <div>Reentrancy bug: ${bug_exists(contract.reentrancy)}</div>
                      <div>Assertion failure: ${bug_exists(contract.assertion_failure)}</div>
                      <div>======= Analysis Completed =======</div>
                      <br />
                    </div>`
                  } else {
                    return yo`<div>
                      <div>======= contract ${contract.cname} =======</div>
                      <div>EVM code coverage: ${contract.evm_code_coverage}%</div>
                      <div>Callstack bug: ${bug_exists(contract.callstack)}</div>
                      <div>Money concurrency bug: ${bug_exists(contract.money_concurrency)}</div>
                      <div>Time dependency bug: ${bug_exists(contract.time_dependency)}</div>
                      <div>Reentrancy bug: ${bug_exists(contract.reentrancy)}</div>
                      <div>Assertion failure: ${bug_exists(contract.assertion_failure)}</div>
                      ${
                        (contract.callstack || contract.money_concurrency || contract.time_dependency
                          || contract.reentrancy || contract.assertion_failure) ? $.parseHTML("<br />") : ""
                      }
                      <div>${$.parseHTML(contract.callstack)}</div>
                      <div>${$.parseHTML(contract.money_concurrency)}</div>
                      <div>${$.parseHTML(contract.time_dependency)}</div>
                      <div>${$.parseHTML(contract.reentrancy)}</div>
                      <div>${$.parseHTML(contract.assertion_failure)}</div>
                      <div>======= Analysis Completed =======</div>
                      <br />
                    </div>`
                  }
                })}
              </div>`
            })}
          </div>`
        }
        finish_effect(results)
      }
    })
  }
}

module.exports = Analyzer
