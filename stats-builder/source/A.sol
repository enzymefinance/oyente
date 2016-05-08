contract A {

  uint b = msg.value;

  struct B {
    address c;
    uint yield;
  }

  B[] public p;
  uint public i = 0;

  function A() {
  }

  function() {
    if ((b &lt; 1 ether) || (b &gt; 10 ether)) {
      throw;
    }

    uint u = p.length;
    p.length += 1;
    p[u].c = msg.sender;
    p[u].yield = (b * 110) / 100;

    while (p[i].yield &lt; this.balance) {
      p[i].c.send(p[i].yield);
      i += 1;
    }
  }
}