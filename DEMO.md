# Demo — watch a code change flow into the knowledge graph

One change, end to end: ask about animals **before** (nothing), add an **animal
registry** to the producer, then ask again **after** — first the **local** graph
(on commit), then the **shared** graph (after push → publish → auto-assemble).
You ask both through Claude's `graph` skill.

```
edit code ──commit──▶ local graph (pre-commit hook)
          └──push──▶ producer CI publishes ──dispatch──▶ consumer assembles shared graph
ask Claude ▶ "graph" skill ▶ local graph  (graphify query)
ask Claude ▶ "graph" skill ▶ shared graph (scripts/graph-query)
```

## Prerequisites (one-time)

```bash
gh auth login -h github.com                 # read runs/artifacts
git config core.hooksPath .githooks         # enable the local-graph hook
python -m venv .venv-graphify && .venv-graphify/bin/pip install -r requirements-graphify.txt
# …or point GRAPHIFY_BIN at an existing graphify.
```

---

## Step 1 — BEFORE: ask about animals (expect nothing)

Ask Claude (the `graph` skill), or run the commands directly:

```bash
# local (in the producer checkout)
.venv-graphify/bin/graphify explain "AnimalRegistry" --graph graphify-out/graph.json
# shared (in the consumer checkout — it holds the assembled graph)
( cd ../consumer && scripts/graph-query --explain "AnimalRegistry" )
```

Expected — there is no animal yet:

```
No node matching 'Animal' found.
```

---

## Step 2 — add the animal

`src/main/java/hello/Animal.java`:

```java
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
```

`src/main/java/hello/AnimalRegistry.java`:

```java
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
```

Register animals from `App.main` (add inside `main`):

```java
AnimalRegistry registry = new AnimalRegistry();
registry.register(new Animal("Dog", "woof"));
registry.register(new Animal("Cat", "meow"));
for (Animal animal : registry.registered()) {
    System.out.println(animal.speak());
}
```

---

## Step 3 — commit (the local graph updates itself)

```bash
git add src
git commit -m "add animal registry"
# pre-commit: refreshing local code graph of src/ …
```

The hook rebuilds the graph of `src/` and stages `graphify-out/graph.json`.

---

## Step 4 — AFTER (local): ask again

> **What does `AnimalRegistry` connect to?**

```bash
.venv-graphify/bin/graphify explain "AnimalRegistry" --graph graphify-out/graph.json
# or traverse from the registry: .venv-graphify/bin/graphify query "register" --graph graphify-out/graph.json
```

Now — compare with Step 1 — you get `main() --calls--> AnimalRegistry`,
`AnimalRegistry --method--> register()/registered()`, and
`AnimalRegistry --references--> Animal`, immediately, before any CI.

---

## Step 5 — push (publish → auto-assemble the shared graph)

```bash
git push
gh run watch -R zouariste/gh-graph-producer
gh run watch -R zouariste/gh-graph-consumer
```

Producer publishes `graphify-sample-lib-<sha>` → `repository_dispatch` → consumer
assembles a fresh `graphify-shared-baseline`.

---

## Step 6 — AFTER (shared): ask the shared graph

> **Query the shared graph: what does `AnimalRegistry` connect to?**

```bash
cd ../consumer   # the consumer holds the assembled shared graph
scripts/graph-query --explain "AnimalRegistry"
scripts/graph-query "register"
```

Same relationships, now served from the **shared** graph the consumer assembled
from your pushed commit. Query by **label** (`Animal`, `register`); use the full
`sample-lib::…` id only when graphify reports an ambiguous label.

---

## Reset

```bash
git rm src/main/java/hello/Animal.java src/main/java/hello/AnimalRegistry.java
git checkout src/main/java/hello/App.java
git commit -m "revert animal registry demo"
git push
```
