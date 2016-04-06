contract foo{	
	function fo() returns (int) {
		 return bar(256);
	}

	function bar(int d) returns (int) {
		return d+1;
	}	
}
