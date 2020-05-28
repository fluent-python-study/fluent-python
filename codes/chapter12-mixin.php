<?php
	trait Hello {
		public function sayHello(){
			echo 'Hello World!';
		}
	}

	class Test {
		use Hello;
	}

	$test = new Test;
	echo $test->sayHello();
?>
