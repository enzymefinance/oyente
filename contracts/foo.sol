contract foo2{	
	function foo() returns (int) {
		 return bar(256) + 123123123;
	}

	function bar(int d) returns (int) {
			int f = 23223232;
    		 return f+1;
	}	
}