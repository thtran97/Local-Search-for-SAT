''''''

# References
# [1] B. Selman, H. Levesque, and D. Mitchell, “A New Method for Solving Hard Satisfiability Problems,” Proc. Tenth Natl. Conf. Artif. Intell., no. July, pp. 440–446, 1992.

''''''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class WalkSAT_Tabu(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose, SKC = True, random_walk = False, noise_parameter = 0.2, tabu_length=None):
        super(WalkSAT_Tabu, self).__init__(input_cnf_file, verbose)
        self.SKC = SKC
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
                    - Choose a variable x which minimizes break count in this unsat clause to flip
                    - When integrating a tabu list, first find an unsat clause that has at least 1 non-tabu variable
                    - Otherwise pick next clause
                    - When all candidates are tabus => ignore tabu list 
                    '''
                    list_id_unsat_clauses = self.id_unsat_clauses.copy() ## Attention: Copy a list => avoid destroying original list  
                    unsat_clause = []
                    while len(unsat_clause) == 0 and len(list_id_unsat_clauses) > 0:
                        random_id = random.choice(list_id_unsat_clauses)
                        list_id_unsat_clauses.remove(random_id)
                        unsat_clause = self.list_clauses[random_id].copy() ## Attention: Copy list !
                        for literal in unsat_clause:
                            if abs(literal) in self.tabu_list:
                                unsat_clause.remove(literal)            
                    if len(unsat_clause) == 0: #ignore
                        random_id =  random.choice(self.id_unsat_clauses)
                        unsat_clause = self.list_clauses[random_id]
                    assert len(unsat_clause) > 0
                    '''
                    Compute "break-count" 
                    '''
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
                    '''
                    Flip chosen variable 
                    Add this variable to taby list 
                    '''
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

    
