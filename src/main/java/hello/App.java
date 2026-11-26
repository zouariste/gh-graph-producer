package hello;

public class App {
    public static void main(String[] args) {
        Greeter greeter = new Greeter("world");
        System.out.println(greeter.greet());

        Farewell farewell = new Farewell("world");
        System.out.println(farewell.bye());
    }
}
