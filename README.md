# Walk-SAT

This repo is an (re)implementation of LS-based SAT Solver, in which a typical algorithm is WalkSAT. 
Let's start !!

Some core functions of this solver are: 

- [X] Generator => generate randomly a truth function
- [X] Checker => verify if assignment satisfies the formula
- [X] Detector => pick an (or all) UNSAT clause(s)
- [X] Evaluator => compute the break-count when flipping a variable
- [X] Stopping criterion 

The main pipeline is:

1- Generate an assignment 
2- Check if SAT or not. If SAT => Done
3- If UNSAT, pick (intelligently or magically) 'best' variable to flip. Repeat 2. 

The algorithm only stop only when formula is SAT or after a defined number of tries and flips. That's why the result is either SAT or UNKNOWN -> not sure if the instances are UNSAT...

The main computation cost is of checker-part : check if assignment satifies formula, i.e. **X |= F**. 
Besides, assigment **X' = flipping(X)** => the difference is only one variable => how can we save computational cost in checking **X' |= F**?
In addition, how can we compute efficiently break-count and make-count of a variable *x*

## TODO
Implement other heuristics for choosing unsat clause and variable to flip ! 