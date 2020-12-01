'''
References
[1] B. Selman, H. Kautz, and B. Cohen, “Noise strategies for local search,” AAAI/IAAI Proc., no. 1990, pp. 337–343, 1994.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class WalkSAT(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose, SKC = True, random_walk = False, noise_parameter = 0.2):
        super(WalkSAT, self).__init__(input_cnf_file, verbose)
        self.SKC = SKC
        self.random_walk = random_walk
        self.noise_parameter = noise_parameter

    def pick_unsat_clause(self):
        assert len(self.id_unsat_clauses) > 0
        random_index = random.choice(self.id_unsat_clauses)
        return self.list_clauses[random_index]

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
                    - WalkSAT idea 
                    - Among all variables that occur in unsat clauses, pick one randomly ! (=> Diverisification)
                    - Choose a variable x which minimizes "break count" in this unsat clause to flip
                    '''
                    unsat_clause = self.pick_unsat_clause()
                    break_count = []
                    for literal in unsat_clause:
                        break_count.append(self.evaluate_breakcount(literal, bs=1, ms=0))
                    '''
                    Original WalkSAT proposed by Selman, Kautz, and Cohen (1994).
                    "never make a random move if there exists one literal with zero break-count"
                    '''
                    if self.SKC and (0 in break_count):
                        x = unsat_clause[break_count.index(0)]
                    else:
                        '''
                        Random walk
                        '''
                        if self.random_walk:
                            p = random.random()
                            if p < self.noise_parameter: # pick x randomly from literals in all unsat clause
                                x = random.choice(unsat_clause)
                            else: 
                                x = unsat_clause[np.argmin(break_count)]
                        else:
                            x = unsat_clause[np.argmin(break_count)]
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

    
