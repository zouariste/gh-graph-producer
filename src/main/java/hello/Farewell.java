package hello;

public class Farewell {
    private final String name;

    public Farewell(String name) {
        this.name = name;
    }

    public String bye() {
        return "Goodbye, " + name + "!";
    }
}
