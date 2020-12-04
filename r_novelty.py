'''
References
[1] D. McAllester, B. Selman, and H. Kautz, “Evidence for invariants in local search,” Proc. Natl. Conf. Artif. Intell., pp. 321–326, 1997.
[2] H. H. Hoos and T. Stützle, “Towards a characterization of the behaviour of stochastic local search algorithms for SAT,” Artif. Intell., vol. 112, no. 1, pp. 213–232, 1999, doi: 10.1016/S0004-3702(99)00048-X.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class R_Novelty(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose, noise_parameter = 0.2, random_walk_noise = None):
        super(R_Novelty, self).__init__(input_cnf_file, verbose)
        self.noise_parameter = noise_parameter
        self.most_recent = None
        # Introduce random walk noise parameter => Novelty+
        self.random_walk_noise = random_walk_noise

    def solve(self):
        initial =  time.time()
        self.initialize_pool()
        while self.nb_tries < self.MAX_TRIES and not self.is_sat:
            self.generate()
            self.initialize_cost()
            self.most_recent = None
            while self.nb_flips < self.MAX_FLIPS and not self.is_sat:
                if self.check() == 1: # if no unsat clause => finish
                    self.is_sat = True
                else:
                    assert len(self.id_unsat_clauses) > 0 
                    '''
                    - GSAT idea (Intensification => focus on best var)
                    - Among all variables that occur in unsat clauses
                    - Choose a variable x which minimizes cost to flip
                    '''
                    all_unsat_lits = []
                    for ind in self.id_unsat_clauses:
                        all_unsat_lits += self.list_clauses[ind]
                    all_unsat_lits = list(set(all_unsat_lits)) # flatten & remove redundants
                    '''
                    Compute cost when flipping each literal 
                        cost = break - make
                    Best var with min cost
                    '''
                    cost = []
                    for literal in all_unsat_lits:
                        cost.append(self.evaluate_breakcount(literal, bs=1, ms=1))
                    '''
                    Random walk
                    '''
                    apply_r_novelty =  True
                    if self.random_walk_noise is not None:
                        wp = random.random()
                        if wp < self.random_walk_noise:
                            x = random.choice(all_unsat_lits)
                            apply_r_novelty = False
                    '''
                    [R_Novelty strategy]
                    Arrange variables according to each cost
                    (1) If the best one *x1* is NOT the most recently flipped variable => select *x1*. 
                    Otherwise, let n = |cost(x1) - cost(x2)| >= 1. Then if:
                    (2a) p < 0.5 & n > 1  => pick *x1*

                    (2b) p < 0.5 & n = 1  => pick *x2* with probability 2p, otherwise *x1*

                    (2c) p >= 0.5 & n = 1 => pick *x2*

                    (2d) p >= 0.5 & n > 1 => pick *x2* with probability 2(p-0.5), otherwise *x1*                    
                    '''
                    if apply_r_novelty:
                        if len(all_unsat_lits) == 1: 
                            x = all_unsat_lits[0]
                        else: 
                            best_id = np.argmin(cost)
                            best_cost = cost[best_id]
                            best_var = all_unsat_lits[best_id]
                            ## Need to find second best cost != best cost
                            second_best_id, second_best_cost, second_best_var = best_id, best_cost, best_var
                            while second_best_cost == best_cost and len(cost) > 1:
                                cost.pop(second_best_id)
                                all_unsat_lits.remove(second_best_var)
                                second_best_id= np.argmin(cost)
                                second_best_cost = cost[second_best_id]
                                second_best_var = all_unsat_lits[second_best_id]
                            # best_var, second_best_var = all_unsat_lits[0], all_unsat_lits[1]
                            if abs(best_var) != self.most_recent: #(1)
                                x = best_var
                            else:
                                n = abs(best_cost - second_best_cost)
                                p = random.random()
                                if n == 0: # all variables has the same cost => pick randomly as Novelty
                                    if p < self.noise_parameter: #(2a)
                                        x = second_best_var
                                    else: #(2b)
                                        x = best_var
                                else: 
                                    '''
                                    R-Novelty's core idea, with n>=1
                                    '''
                                    if self.noise_parameter < 0.5 and n > 1: 
                                        x = best_var
                                    elif self.noise_parameter < 0.5 and n == 1: 
                                        if p < 2*self.noise_parameter: 
                                            x = second_best_var
                                        else:
                                            x = best_var
                                    elif self.noise_parameter >= 0.5 and n == 1:
                                        x = second_best_var
                                    elif self.noise_parameter >= 0.5 and n > 1:
                                        if p < 2*(self.noise_parameter-0.5):
                                            x = second_best_var
                                        else:
                                            x = best_var
                    ''' 
                    After choosing x, flip it and save this last recent move
                    '''                    
                    self.flip(x) 
                    self.most_recent = abs(x)

        end = time.time()
        print('Nb flips:  {0}      '.format(self.nb_flips))
        print('Nb tries:  {0}      '.format(self.nb_tries))
        print('CPU time:  {0:10.4f} s '.format(end-initial))
        if self.is_sat:
            print('SAT')
            return self.assignment
        else:
            print('UNKNOWN')
            return None

    
