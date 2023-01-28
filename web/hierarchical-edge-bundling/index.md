Stick your data below. Expected in either the CSV format (with each line carrying be a
pair of `parent,child` or `child,parent`; check the right button below) or JSON (each 
key being a parent and corresponding value an array of children
`{parent: [child, child, ...], parent: [...]}`, or a child and
corresponding value an array of parents `{child: [parent, parent, ...], child: [...]}`).
Keep it consistent, no mixing between these formats.

In blue the parent(s), in red the child(ren). Taking the database concepts this was
initially written for, in blue the object(s) the current object depends on, and in red
the object(s) that depend(s) on the current object.

%[depviz ?module](/hierarchical-edge-bundling/script.js)
