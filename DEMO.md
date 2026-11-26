# Demo — watch a code change flow into the knowledge graph

This walks through one change end to end: add an **animal registry** to the
producer, and watch it appear first in the **local** graph (on commit) and then
in the **shared** graph (after push → publish → auto-assemble). You ask both
graphs through Claude's `graph` skill.

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
# a graphify binary — either create the venv once:
python -m venv .venv-graphify && .venv-graphify/bin/pip install -r requirements-graphify.txt
# …or point GRAPHIFY_BIN at an existing one.
```

---

## Step 1 — add an animal

Create `src/main/java/hello/Animal.java`:

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

Create `src/main/java/hello/AnimalRegistry.java`:

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

Register a couple of animals from `App.main` (add inside `main`):

```java
AnimalRegistry registry = new AnimalRegistry();
registry.register(new Animal("Dog", "woof"));
registry.register(new Animal("Cat", "meow"));
for (Animal animal : registry.registered()) {
    System.out.println(animal.speak());
}
```

---

## Step 2 — commit (the local graph updates itself)

```bash
git add src
git commit -m "add animal registry"
```

The pre-commit hook rebuilds the graph of `src/` and stages
`graphify-out/graph.json`, so the committed graph matches the committed code.
You'll see:

```
pre-commit: refreshing local code graph of src/ …
```

---

## Step 3 — ask the LOCAL graph (via Claude)

Open Claude Code in this repo and ask — the `graph` skill answers from the
committed local graph:

> **What registers animals?**

Or run what the skill runs:

```bash
.venv-graphify/bin/graphify query "what registers animals" --graph graphify-out/graph.json
```

Expect `AnimalRegistry.register()` and `App.main() --calls--> register()` — already
present, before any CI.

---

## Step 4 — push (publish → auto-assemble the shared graph)

```bash
git push
```

- The producer CI builds and publishes `graphify-sample-lib-<sha>`.
- It fires a `repository_dispatch` at the consumer, which fetches that artifact,
  validates it, and assembles a fresh `graphify-shared-baseline`.

Watch:

```bash
gh run watch -R zouariste/gh-graph-producer
gh run watch -R zouariste/gh-graph-consumer
```

---

## Step 5 — ask the SHARED graph (via Claude)

Still in Claude, ask for the shared view:

> **Query the shared graph: what registers animals?**

The `graph` skill runs the wrapper, which re-fetches the baseline only because a
new run was published, verifies its checksum, then queries. Or run it directly:

```bash
scripts/graph-query "what registers animals"
scripts/graph-query --explain "Animal"        # ids are prefixed sample-lib::…
```

Expect the same `register` / `speak` relationships — now served from the
**shared** graph that the consumer assembled from your pushed commit.

> Query by **label** (`Animal`, `register`, `speak`). graphify asks for the full
> prefixed id (`sample-lib::…`) only when a label is ambiguous.

---

## Reset

```bash
git rm src/main/java/hello/Animal.java src/main/java/hello/AnimalRegistry.java
git checkout src/main/java/hello/App.java
git commit -m "revert animal registry demo"
git push
```
