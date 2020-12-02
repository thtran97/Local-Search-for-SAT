'''
References
[1] R. Battiti and G. Tecchiolli, “The Reactive Tabu Search,” ORSA J. Comput., vol. 6, no. 2, pp. 126–140, 1994, doi: 10.1287/ijoc.6.2.126.
[2] R. Battiti and M. Protasi, “Reactive Search, a history-based heuristic for MAX-SAT,” ACM J. Exp. Algorithmics, vol. 2, pp. 130–157, 1997, doi: 10.1145/264216.264220.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class H_RTS(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose):
        super(H_RTS, self).__init__(input_cnf_file, verbose)
        '''
        Initialize tabu list and its length
        Note that tabu list is a circular list 
        '''
        self.tabu_list = []
        self.Tf = 0.1
        self.tabu_tenure = 0

    def initialize_tabu(self, tabu_tenure):
        self.tabu_list = []
        self.tabu_tenure = tabu_tenure
        
    def add_tabu(self, literal):
        '''
        Add a move to tabu list
        '''
        if len(self.tabu_list) < self.tabu_tenure:
            self.tabu_list.append(abs(literal))
        else: # tabu list is full
            self.tabu_list.pop(0)
            self.tabu_list.append(literal)

    def hamming_distance(self,a, b):
        c = np.bitwise_xor(a, b)
        n = c.sum()
        return n

    def react(self, X_f, X_i):
        deriv = float(self.hamming_distance(X_f, X_i) / (self.tabu_tenure+1)) -1
        if deriv <= 0:
            self.Tf += 0.01
        elif deriv > 0.5:
            self.Tf -= 0.01
        if self.Tf > 0.25:
            self.Tf = 0.25
        elif self.Tf < 0.025:
            self.Tf = 0.025
        return max(int(self.Tf*self.nvars), 4)

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
            self.Tf = 0.1
            self.tabu_tenure = int(self.Tf * self.nvars)
            '''
            TODO: NOB_LS here
            '''
            while self.nb_flips < self.MAX_FLIPS and not self.is_sat:
                '''
                [Local Search]
                - GSAT idea (Intensification => focus on best var)
                - Among all variables that occur in unsat clauses
                - Choose a variable x which minimizes cost to flip
                - Compute cost when flipping each literal 
                - Cost = break - make
                - After flipping, check if the nb of UNSAT clause decreases or not
                - Yes => continuer
                - No => stop at local optimum
                '''
                improved = True
                while improved and self.nb_flips < self.MAX_FLIPS and not self.check():  
                    all_allowed_lits = self.pick_all_lits(self.id_unsat_clauses)
                    break_make_count = []
                    for literal in all_allowed_lits:
                        break_make_count.append(self.evaluate_breakcount(literal, bs=1, ms=1))
                    nb_unsat = len(self.id_unsat_clauses)
                    if nb_unsat + min(break_make_count) < nb_unsat:
                        x = all_allowed_lits[np.argmin(break_make_count)]
                        self.flip(x)
                    else: 
                        improved = False
                X_i = self.assignment.copy()
                if self.check():
                    self.is_sat =  True
                    break
                '''
                [Reactive Tabu Search] 
                - Initialize tabu list with defined tabu tenure
                - Compute new X after 2(T+1) iterations with TS
                    + Remove all tabus in list of candidates
                    + If all vars are tabu => ignore tabu and take initial list of variables
                - Update tabu tenure
                '''
                it = 0
                while not self.check() and it < 2*(self.tabu_tenure+1):
                    # compute allowed literals wrt tabu list
                    all_allowed_lits = self.pick_all_lits(self.id_unsat_clauses, self.tabu_list)
                    if len(all_allowed_lits) == 0: # else take all_allowed_lits and ignore tabu
                        all_allowed_lits = self.pick_all_lits(self.id_unsat_clauses)
                    break_make_count = []
                    for literal in all_allowed_lits:
                        break_make_count.append(self.evaluate_breakcount(literal, bs=1, ms=1))
                    x = all_allowed_lits[np.argmin(break_make_count)]
                    # '''
                    # Random walk  
                    # '''
                    # if self.random_walk:
                    #     p = random.random()
                    #     if p < self.noise_parameter: # pick x randomly from literals in all unsat clause
                    #         x = random.choice(all_allowed_lits)
                    #     else: 
                    #         x = all_allowed_lits[np.argmin(break_count)]
                    # else:
                    #     x = all_allowed_lits[np.argmin(break_count)]
                    self.flip(x) 
                    self.add_tabu(x)
                    it += 1
                X_f = self.assignment.copy()
                if self.check():
                    self.is_sat=True
                    break
                '''
                Update tabu tenure based on search history
                '''
                self.tabu_tenure = self.react(X_f, X_i)
    
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

    
