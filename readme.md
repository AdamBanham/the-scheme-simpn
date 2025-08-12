# Simulating the Scheme

This repo captures my initial testing of [simpn]() for the purposes of 
simulating a process modelled in BPMN.

## Goals

- Simulate the two phases of the process
    - pre-robodebt
    - oci 
- Work out a way to make the resulting simulation data presentable via 
  a web interface 
- Work out a way to give power to visitor to change the process and see
  how there changes affected the performance of the process

## Progress 

Some good process at the moment. Docuementation of examples in the simpn, 
is a bit light. But talking the code, mostly explains the code. The interaction
of simtokens and simvars still feels a bit foreign to me.

### Initial Thoughts on simPN

Very cool library. The team over in TU/e and Prof. Remco Dikjman have made
something that could be used for simulation of basically anything.

For my personal peference, it initially felt like I was always writing the
plumbing for my modeling rather than declaratively denoting the steps. So
I made some helper classes in [bpmn.py](./bpmn.py) to make my life a bit 
easier. I might take these a step further and have a single wrapper class
and introduce a type name to make it happen once I have gone through all the
prototypes from `simpn.prototypes` related to BPMN.

### Pre-robodebt

I have been playing around with the initial phase of the pre-robodebt process.

![demo of sim](./output.gif)

### OCI

No modeling at the moment.