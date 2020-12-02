# Local Search based algorithms for solving SAT

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

1- Generate an assignment. 

2- Check if SAT or not. If SAT => Done.

3- If UNSAT, pick (intelligently or magically) 'best' variable to flip. Repeat 2. 

## Analytics

The algorithm only stop only when formula is SAT or after a defined number of tries and flips. That's why the result is either SAT or UNKNOWN -> not sure if the instances are UNSAT...

The main computation cost is of checker-part : check if assignment satifies formula, i.e. **X |= F**?.

Besides, assignment **X' = flip(X)** => the difference is only of one variable => how can we save computational cost in (re)checking **X' |= F**?.

In addition, how can we compute efficiently break-count and make-count of a variable *x*?. 

Which variable should be flipped?.

How to escape the stagnation situation?. 

etc. 

## Implementations of LS-based variants

#### 1. GSAT, 1992 :white_check_mark:

***Idea:*** Considering all variables in all unsat clause, then pick the one that minimizes the number of UNSAT clauses => min cost = break - make.

#### 2. GSAT/Random Walk, 1993  :white_check_mark:

***Idea:***  With probability p => pick any variable. Otherwise => pick best local move !. 

#### 3. WalkSAT & WalkSAT/Random Walk, 1994 :white_check_mark:

***Idea:*** Pick (randomly) one UNSAT clause, then pick the variable that minimizes break => score = break. In addition, the original strategy of Selman, Kautz, and Cohen (1994), called SKC stragegy, proposed that: "never make a random move if there exists one literal with zero break-count". Obviously, flipping literal with zero break-count will improve the objective function (= number of SAT clauses).

#### 4. GSAT/Tabu & WalkSAT/Tabu, 1997 :white_check_mark:

***Idea:*** Use a tabu list which store (flipped variables, tabu tenures) to avoid repeating these last recent moves. Intuitively, a couple *(x,t)* means that we forbid flipping *x* for next *t* iterations ! More concretely,

- Refuse flipping a variable in tabu list

- In case of *WalkSAT/Tabu*, if all the variables in the chosen UNSAT clause are tabu => choose another UNSAT clause instead

- If all variables in all UNSAT clauses are tabu =>  tabu list is temporarily ignored

In general, tabu list should be implemented as a FIFO circular list => tabu tenure *t* is fixed (i.e. the length of tabu list) during the search. However, tabu tenure can also be dynamically changed during search in a more complex variant (Reactive Tabu Search, we will see it later).


#### 5. Hamming-Reactive Tabu Search (H-RTS), 1997 :white_check_mark:

***Idea:***  Tabu tenure T(t) is dynamically changed during the search. More precisely, "T(t) inscreases when repetitions happen and decreases when repititions disappear for a sufficiently long search period". The general pipeline proposed by R.Battiti and M.Prostasi (1997) is:

```python
while stop_trying_criterion is not satisfied: 
    X = random_assignment
    Tf = 0.1            # fractional prohibtion
    T = int(Tf * nvars) # tabu tenure 
    '''
    Non-oblivious LS => find quickly a local optimum
    NOB-LS is similar to OLS, except the objective function used to choose the best variable to flip
    '''
    X = NOB_LS(f_NOB)

    while stop_flipping_criterion is not satisfied:
        '''
        Obvious local search => find a local optimum
        Put simply, use cost = break-make = f_OB
        '''
        X = OLS(f_OB)
        X_I = X
        '''
        Reactive Tabu Search
        - Compute X after 2(T+1) iterations
        - Change dynamically T 
        '''
        for 2(T+1) iterations:
            X = TabuSearch(f_OB)
        X_F = X
        T = react(Tf, X_F, X_I)
```

Note: In fact, the choice of non-obvilious objective function is a challenge wrt different instances. That's why in this implementation, I only use OLS function for finding local the optimum, but theorically, a NOB should be implemented if necessaire. 

***Reactive search => Reinforcement learning for heuristics***

#### 6. Novelty, 1997 :white_check_mark:

***Idea:*** Sort variables according to cost, as does GSAT. Under this specific sort, consider the best *x1* and second-best variable *x2*. 

(1) If the best one *x1* is NOT the most recently flipped variable => select *x1*. 

Otherwise, (2a) select *x2* with probability p, (2b) select *x1* with probability 1-p.

=> Improvements for selecting flipping variables by breaking tie in favor of the least recently variable.

=> Enhance its diversification capacity.         

#### 7. R-Novelty, 1997 :white_check_mark:

***Idea:*** Similar to Novelty, except in case of *x1* is the most recently flipped variable !. 

In this case, let n = |cost(x1) - cost(x2)| >= 1. Then if:

(2a) p < 0.5 & n > 1  => pick *x1*

(2b) p < 0.5 & n = 1  => pick *x2* with probability 2p, otherwise *x1*

(2c) p >= 0.5 & n = 1 => pick *x2*

(2d) p >= 0.5 & n > 1 => pick *x2* with probability 2(p-0.5), otherwise *x1*

Intuitively, the idea behind R_Novelty is that the difference in objective function should influence our choice, i.e. a large difference favors the best one.

- [ ] Influence of noise parameter p ? 

#### 8. Novelty+ & R-Novelty+, 1999 :white_check_mark:

***Idea:*** Introduce Random Walk into Novelty and R-Novelty to prevent the extreme stagnation behavior. With probability wp => pick randomly, otherwise with probability 1-wp, follow the strategy of Novelty and R-Novelty.

#### 9. AdaptNovelty+, 2002 :white_check_mark:

***Idea:*** Adjust the noise parameter wp according to search history, i.e. increase wp when detecting a stagnation behavior. Then decrease wp until the next stagnation situation is detected. Concretely,

- Initialize wp = 0 => greedy search with Novelty strategy

- No improvements over some predefined steps => stagnation detected 

- Increase wp until quit stagnation situation

- Overcome the stagnation => decrease wp until the next stagnation is detected 

Note : dynamic noise parameter of random walk, not the one of Novelty mechanism.

#### 10. Iterated Robust Tabu Search (IRoTS), 2003 :x:

***Idea:*** Combine the performances of both Iterated LS and TS.

- [ ] Read and summarize the idea of original paper's work

#### 11. Adaptive Memory-Based Local Search (AMLS), 2012 :x:

***Idea:*** Combine the stategies of aformentioned heuristics.

## Result and comparation of different strategies 

Let's review some strategies of LS-based SAT Solver by fixing some parameters (MAX_FLIPS = 500, MAX_TRIES = 100, noise_parameter = 0.2) and compare their performance with only medium **SAT instances** (*e.g. uf-20-0x.cnf or uf-50-0x.cnf*). As aforementioned, given UNSAT instances, the results are UNKNOWN. 

## TODO

- [ ] Use 2-flip or 3-flip neighborhoods instead of 1-flip ones

- [ ] Implement other heuristics for choosing unsat clause and variable to flip ! 

- [ ] Find benchmarking dataset (e.g. [SATLIB benchmark](https://www.cs.ubc.ca/~hoos/SATLIB/benchm.html)) and criterions for measuring the performance of a strategy and use it to compare with others

- [ ] Build a test script for comparing performances of all implemented strategies

- [ ] Further idea is to apply Knowledge Compilation techniques so that we can answer consistence query in polynomial time 

- [ ] Involve to Max-SAT & finding Max-SAT benchmarking instancecs
