Pure [D3](https://d3js.org/) implementation.

<details markdown="1">
  <summary>What do I do?</summary>

Stick your data below. Expected in either the CSV format (each line carrying a pair of
`parent,child` or `child,parent`; check the right button below) or JSON (each key being
a parent and corresponding value an array of children
`{parent: [child, child, ...], parent: [...]}`, or a child and corresponding value an
array of parents `{child: [parent, parent, ...], child: [...]}`). Keep it consistent, no
mixing between these formats.

</details>

In blue the parent(s), in red the child(ren). Taking the database concepts this was
initially written for, in blue the object(s) the current object depends on, and in red
the object(s) that depend(s) on the current object.

%[depviz ?module](/hierarchical-edge-bundling/script.js)
