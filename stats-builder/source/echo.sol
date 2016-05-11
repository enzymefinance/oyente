// 0x6896ad514a2ce7586762f8e641c7821827a255c1
// 0.0
contract echo {
  /* Constructor */
  function () {
    msg.sender.send(msg.value);
  }
}