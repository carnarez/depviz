Stick your data below. Expected in either the CSV format (each line carrying a pair of
`parent,child` or `child,parent`; check the right button below) or JSON (each key being
a parent and corresponding value an array of children
`{parent: [child, child, ...], parent: [...]}`, or a child and corresponding value an
array of parents `{child: [parent, parent, ...], child: [...]}`). Keep it consistent, no
mixing between these formats.

The resulting `DOT` code will be dumped to the console.

You have to keep it reasonable in term of number of objects (_aka_ nodes) involved or
the diagram will be unreadable.

%[depviz ?module](/graphviz-graph/script.js)
