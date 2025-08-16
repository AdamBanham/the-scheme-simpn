# Profiling

To run profiling on a script, use the following commands
```bash
 py -m cProfile -o [out-file].prof [script-file].py
```
or 
```bash
py -m cProfile -o tut-bpmn-02-2.prof tut-bpmn-02.py
```

Then once the `.prof` is produced, with the flamegraph python module, see https://github.com/brendangregg/FlameGraph and https://github.com/baverman/flameprof, I can make a flame graph.

Use the following command on to create the svg:
```bash
flameprof [out-file].prof > [svg-file].svg
```
or 
```bash
py -m flameprof tut-bpmn-02-2.prof > tut-bpmn-02-2-prof.svg
```