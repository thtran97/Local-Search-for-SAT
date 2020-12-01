# Walk-SAT

This repo is an (re)implementation of LS-based SAT Solver, in which a typical algorithm is WalkSAT. 
Let's start !!

## Core functions 

Some core functions of this solver are: 

- [X] Generator => generate randomly a truth function
- [X] Checker => verify if assignment satisfies the formula
- [X] Detector => pick an (or all) UNSAT clause(s)
- [X] Evaluator => compute the break-count when flipping a variable
- [X] Stopping criterion 

***Comment:*** In my opinion, implementation of WalkSAT is much more easier than CDCL-based solver :) 

## General pipeline

The main pipeline is:

1- Generate an assignment 

2- Check if SAT or not. If SAT => Done

3- If UNSAT, pick (intelligently or magically) 'best' variable to flip. Repeat 2. 

## Analytics

The algorithm only stop only when formula is SAT or after a defined number of tries and flips. That's why the result is either SAT or UNKNOWN -> not sure if the instances are UNSAT...

The main computation cost is of checker-part : check if assignment satifies formula, i.e. **X |= F**?

Besides, assignment **X' = flipping(X)** => the difference is only one variable => how can we save computational cost in checking **X' |= F**?

In addition, how can we compute efficiently break-count and make-count of a variable *x*? 

Which variable should be flipped?

How to escape the stagnation situation? 

etc. 

## Implementations of LS-based variants

#### 1. GSAT, 1992 :white_check_mark:

***Idea:*** Considering all variables in all unsat clause, then pick the one that minimizes the number of UNSAT clauses => min cost = break - make

***Result:*** Nb of max flips and max tries are too small to find a SAT solution => the result is UNKNOWN ! 

#### 2. GSAT/Random Walk, 1993  :white_check_mark:

***Idea:***  With probability p => pick any variable. Otherwise => pick best local move ! 

***Result:*** However, GSAT with random walk (certainly with prefixed parameters of MAX_TRIES and MAX_FLIPS) still return UNKNOWN => need more iterations... maybe...

#### 3. WalkSAT & WalkSAT/Random Walk, 1994 :white_check_mark:

***Idea:*** Pick (randomly) one UNSAT clause, then pick the variable that minimizes break => score = break. In addition, the original strategy of Selman, Kautz, and Cohen (1994), called SKC stragegy, proposed that: "never make a random move if there exists one literal with zero break-count". Obviously, flipping literal with zero break-count will improve the objective function (= number of SAT clauses).

***Result:*** Given a SAT instance, result is correctly SAT. WalkSAT with random walk returns output slightly faster and less number of tries. 

#### 4. GSAT/Tabu & WalkSAT/Tabu, 1997 :x:

***Idea:*** Use a tabu list which store (flipped variables, tabu tenures) to avoid repeating these last recent moves. Intuitively, a couple *(x,t)* means that we forbid flipping *x* for next *t* iterations ! 

Note that tabu list should be implemented as a FIFO circular list.  

***Parameter choice:***

- Length of tabu list => fixed tabu tenure

***Result:*** 

#### 5. Novelty, 1997 :x:

***Idea:*** Under a specific sort (?), consider the best *x1* and second-best variable *x2*. (1) If the best one *x1* is NOT the most recently flipped variable => select *x1*. Otherwise, (2a) select *x2* with probability p, (2b) select *x1* with probability p-1

***Result:***

#### 6. R-Novelty, 1997 :x:

***Idea:*** Similar to Novelty, except in case of *x1* is the most recently flipped variable ! 

In this case, let n = |cost(x1) - cost(x2)| >= 1. Then:

(2a) p < 0.5 & n > 1  => pick *x1*

(2b) p < 0.5 & n = 1  => pick *x2* with probability 2p, otherwise *x1*

(2c) p >= 0.5 & n = 1 => pick *x2*

(2d) p >= 0.5 & n > 1 => pick *x2* with probability 2(p-0.5), otherwise *x1*

Intuitively, the idea behind R_Novelty is that the difference in objective function should influence our choice, i.e. a large difference favors the best one.

#### 7. Novelty+ & R-Novelty+, 1999 :x:

***Idea:*** Introduce Random Walk into Novelty and R-Novelty to prevent the extreme stagnation behavior. With probability wp => pick randomly, otherwise with probability 1-wp, follow the strategy of Novelty and R-Novelty.

#### 8. AdaptNovelty+, 2002 :x:

***Idea:*** Adjust the noise parameter p according to search history, i.e. increase p when detecting a stagnation behavior. Then decrease p until the next stagnation situation is detected.

#### 9. Reactive Tabu Search (H-RTS), 1997 :x:

***Idea:***  Tabu tenure is dynamically changed during the search.

#### 10. Iterated Reactive Tabu Search (IRoTS), 2003 :x:

***Idea:*** Combine the performances of both approaches

#### 11. Adaptive Memory-Based Local Search (AMLS), 2012 :x:

***Idea:*** Combine the stategies of aformentioned heuristics.

## Result and comparation of different strategies 

Let's review some strategies of LS-based SAT Solver by fixing some parameters (MAX_FLIPS = 500, MAX_TRIES = 100, noise_parameter = 0.2) and compare their performance with only medium **SAT instances** (*e.g. uf-20-0x.cnf or uf-50-0x.cnf*). As aforementioned, given UNSAT instances, the results are UNKNOWN. 

## TODO

- [ ] Implement other heuristics for choosing unsat clause and variable to flip ! 

- [ ] Further idea is to apply Knowledge Compilation techniques so that we can answer consistence query in polynomial time 

