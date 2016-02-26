contract foo {
	function foos(int d) returns (int) {
  		d += 3;
    	return (d+999);
	}

	function bar(int d) returns (int) {
    	return (d*100);
	}

	function bar2(int b) {
		b = 10;
	}
}