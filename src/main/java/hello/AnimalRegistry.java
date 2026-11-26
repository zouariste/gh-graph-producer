package hello;

import java.util.ArrayList;
import java.util.List;

public class AnimalRegistry {
    private final List<Animal> animals = new ArrayList<>();

    public void register(Animal animal) {
        animals.add(animal);
    }

    public List<Animal> registered() {
        return animals;
    }
}
