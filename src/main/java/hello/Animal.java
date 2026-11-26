package hello;

public class Animal {
    private final String name;
    private final String sound;

    public Animal(String name, String sound) {
        this.name = name;
        this.sound = sound;
    }

    public String name() {
        return name;
    }

    public String speak() {
        return name + " says " + sound;
    }
}
