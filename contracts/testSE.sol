contract foo {
	function bar(int d) returns (int) {
		 var x = 0;
		 if (d > 0) {
		    x = x + 1;
		 }
		 if (d <= -1) {
		    x = x + 2;
		 }
		 return x;
	}
}