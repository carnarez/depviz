The implementation below is based on the
[`3d-force-graph`](https://github.com/vasturiano/3d-force-graph) package, itself carried
by [`three.js`](https://github.com/mrdoob/three.js) and its
[WebGL](https://www.khronos.org/webgl/) rendering.

<details markdown="1">
  <summary>What do I do?</summary>

Stick your data below. Expected in either the CSV format (each line carrying a pair of
`parent,child` or `child,parent`; check the right button below) or JSON (each key being
a parent and corresponding value an array of children
`{parent: [child, child, ...], parent: [...]}`, or a child and corresponding value an
array of parents `{child: [parent, parent, ...], child: [...]}`).

Keep it consistent, no mixing between these formats.

Use the checkbox if you want to _explicitely_ show the node names instead of keeping
them as hovered labels. Keep it mind that might become unreadable for large number of
nodes.

In blue the parent(s), in red the child(ren). Taking the database concepts this was
initially written for, in blue the object(s) the current object depends on, and in red
the object(s) that depend(s) on the current object.

</details>

To get out of the 3D representation simply refresh the page or use the table of contents
(top-left button) to navigate to another page.

%[depviz](/force-directed-graph/script.js)
