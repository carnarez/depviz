Diagram generated via the [`Mermaid`](https://github.com/mermaid-js/mermaid) package
([docs](https://mermaid.js.org/)). Guaranteed clean syntax definition, but cumbersome
to style!

<details markdown="1">
  <summary>What do I do?</summary>

Stick your data below. Expected in either the CSV format (each line carrying a pair of
`parent,child` or `child,parent`; check the right button below) or JSON (each key being
a parent and corresponding value an array of children
`{parent: [child, child, ...], parent: [...]}`, or a child and corresponding value an
array of parents `{child: [parent, parent, ...], child: [...]}`). Keep it consistent, no
mixing between these formats.

Diagram orientation can be selected using the arrows below (click on your choice). The
resulting `Mermaid` code will be dumped to the console.

You have to keep it reasonable in term of number of objects (_aka_ nodes) involved or
the diagram will be unreadable.

</details>

%[depviz ?module](/mermaid-flowchart/script.js)
