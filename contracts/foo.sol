contract foo{	
	function foo() {
		 return bar(256);
	}

	function bar(int d) {
		if (now >= now+1) 
		    msg.sender.send(100);		  
	}	
}
