'''
References
[1] B. Selman, H. Levesque, and D. Mitchell, “A New Method for Solving Hard Satisfiability Problems,” Proc. Tenth Natl. Conf. Artif. Intell., no. July, pp. 440–446, 1992.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class GSAT(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose, random_walk = False, noise_parameter = 0.2):
        super(GSAT, self).__init__(input_cnf_file, verbose)
        self.random_walk = random_walk
        self.noise_parameter = noise_parameter

    def solve(self):
        initial =  time.time()
        self.initialize_pool()
        while self.nb_tries < self.MAX_TRIES and not self.is_sat:
            self.generate()
            self.initialize_cost()
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
                    Cost = break - make
                    '''
                    break_count = []
                    for literal in all_unsat_lits:
                        break_count.append(self.evaluate_breakcount(literal, bs=1, ms=1))
                    '''
                    Random walk  
                    '''
                    if self.random_walk:
                        p = random.random()
                        if p < self.noise_parameter: # pick x randomly from literals in all unsat clause
                            x = random.choice(all_unsat_lits)
                        else: 
                            x = all_unsat_lits[np.argmin(break_count)]
                    else:
                        x = all_unsat_lits[np.argmin(break_count)]
                    self.flip(x) 

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

    
