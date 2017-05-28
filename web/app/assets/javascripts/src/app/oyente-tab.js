var yo = require('yo-yo')

// -------------- styling ----------------------
var csjs = require('csjs-inject')
var styleGuide = require('./style-guide')
var styles = styleGuide()

var css = csjs`
  .oyenteTabView {
    padding: 2%;
  }
  .crow {
    margin-top: 1em;
    display: flex;
  }
  .options {
    margin-top: 1em;
    display: block;
  }
  .select extends ${styles.dropdown} {
    float: left;
    max-width: 90%;
  }
  .button extends ${styles.button} {
    background-color: #C6CFF7;
    width: 100%;
    align-self: center;
    text-align: -webkit-center;
  }
  .result extends ${styles.infoTextBox} {
    margin-top: 2em;
  }
`

module.exports = oyenteTab

function oyenteTab () {
  return yo`
    <div class="${css.oyenteTabView}" id="oyenteView">
      <div class="${css.options}" id="oyente-options"></div>
      <div class="${css.crow}">
        <div class="${css.button}" id="analyzer" title="Analyze source code's security">
          <i class="fa fa-search" aria-hidden="true"></i>
          Analyze
        </div>
      </div>
      <div id="analysis" class="${css.result}" hidden></div>
    </div>
  `
}
