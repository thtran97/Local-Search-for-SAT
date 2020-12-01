'''
References
[1] D. McAllester, B. Selman, and H. Kautz, “Evidence for invariants in local search,” Proc. Natl. Conf. Artif. Intell., pp. 321–326, 1997.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class Novelty(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose, noise_parameter = 0.2):
        super(Novelty, self).__init__(input_cnf_file, verbose)
        self.noise_parameter = noise_parameter
        self.most_recent = None

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
                    [Novelty strategy]
                    Arrange variables according to each cost
                    (1) If the best one *x1* is NOT the most recently flipped variable => select *x1*. 
                    Otherwise, 
                    (2a) select *x2* with probability p, 
                    (2b) select *x1* with probability 1-p.
                    '''
                    if len(all_unsat_lits) == 1: 
                        x = all_unsat_lits[0]
                    else: 
                        best_id = np.argmin(cost)
                        best_var = all_unsat_lits[best_id]
                        cost.pop(best_id)
                        all_unsat_lits.remove(best_var)
                        second_best_id = np.argmin(cost)
                        second_best_var = all_unsat_lits[second_best_id]
                        # best_var, second_best_var = all_unsat_lits[0], all_unsat_lits[1]
                        if abs(best_var) != self.most_recent: #(1)
                            x = best_var
                        else:
                            p = random.random()
                            if p < self.noise_parameter: #(2a)
                                x = second_best_var
                            else: #(2b)
                                x = best_var
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

    
