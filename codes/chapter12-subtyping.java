/**
일반적으로 하나의 파일에는 하나의 클래스만 선언
해당 파일을 실행하는 방법
1. 파일의 경로에서 javac  12-subtyping.java 명령어를 통해서 컴파일
2. java Main 명령어를 통해 실행
*/
class Main {
	public static void main(String[] args) {
		A subtypeTest = new B();
		subtypeTest.printHello();
	}
}

class A {
	public void printHello(){
		System.out.println("Hello World!");
	}
}

class B extends A {
}
