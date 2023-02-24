The implementation below makes use of the
[`d3-dag`](https://github.com/erikbrinkman/d3-dag) package. Check some examples on
[Observable](https://observablehq.com/search?query=d3-dag).

<details markdown="1">
  <summary>What do I do?</summary>

Stick your data below. Expected in either the CSV format (each line carrying a pair of
`parent,child` or `child,parent`; check the right button below) or JSON (each key being
a parent and corresponding value an array of children
`{parent: [child, child, ...], parent: [...]}`, or a child and corresponding value an
array of parents `{child: [parent, parent, ...], child: [...]}`). Keep it consistent, no
mixing between these formats.

Make sure all objects present in the data are connected somehow! Otherwise `d3-dag` gets
into some kind of infinite loop...

</details>

WORK IN PROGRESS

%[depviz](/directed-acyclic-graph/script.js)
