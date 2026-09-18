Exploration only.

Nothing in this directory is imported by anything in `src/`. If a notebook
produces something worth keeping, it moves into `src/` as a real module with a
test. Notebooks that pipelines depend on are the single most common reason a
data project stops being reproducible.
