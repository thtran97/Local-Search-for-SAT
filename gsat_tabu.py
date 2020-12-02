'''
References
[1] D. McAllester, B. Selman, and H. Kautz, “Evidence for invariants in local search,” Proc. Natl. Conf. Artif. Intell., pp. 321–326, 1997.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class GSAT_Tabu(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose, random_walk = False, noise_parameter = 0.2, tabu_length=None):
        super(GSAT_Tabu, self).__init__(input_cnf_file, verbose)
        self.random_walk = random_walk
        self.noise_parameter = noise_parameter
        '''
        Initialize tabu list and its length
        Note that tabu list is a circular list 
        '''
        if tabu_length is None:
            self.tabu_length = int(0.01875*self.nvars + 2.8125)
        else:
            self.tabu_length = tabu_length
        self.tabu_list = []

    def add_tabu(self, literal):
        '''
        Add a move to tabu list
        '''
        if len(self.tabu_list) < self.tabu_length:
            self.tabu_list.append(abs(literal))
        else: # tabu list is full
            self.tabu_list.pop(0)
            self.tabu_list.append(literal)

    def pick_all_lits(self,id_unsat_clauses, tabu_list=None):
        all_allowed_lits = []
        for ind in id_unsat_clauses:
            all_allowed_lits += self.list_clauses[ind]   
        if tabu_list is not None:
            all_allowed_lits = list(set(all_allowed_lits)^set(tabu_list))
        else:
            all_allowed_lits = list(set(all_allowed_lits))
        return all_allowed_lits

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
                    # compute allowed literals wrt tabu list
                    all_allowed_lits = self.pick_all_lits(self.id_unsat_clauses, self.tabu_list)
                    if len(all_allowed_lits) == 0: # else take all_allowed_lits and ignore tabu
                        all_allowed_lits = self.pick_all_lits(self.id_unsat_clauses)
                    '''
                    Compute cost when flipping each literal 
                    Cost = break - make
                    '''
                    break_count = []
                    for literal in all_allowed_lits:
                        break_count.append(self.evaluate_breakcount(literal, bs=1, ms=1))
                    '''
                    Random walk  
                    '''
                    if self.random_walk:
                        p = random.random()
                        if p < self.noise_parameter: # pick x randomly from literals in all unsat clause
                            x = random.choice(all_allowed_lits)
                        else: 
                            x = all_allowed_lits[np.argmin(break_count)]
                    else:
                        x = all_allowed_lits[np.argmin(break_count)]
                    
                    self.flip(x) 
                    self.add_tabu(x)
        
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

    
