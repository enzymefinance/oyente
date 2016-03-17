contract testOwner {

	 function kill() {
	 	  suicide(msg.sender);
	 }
}