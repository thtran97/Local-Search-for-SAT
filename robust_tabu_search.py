'''
References
[1] K. Smyth, H. H. Hoos, and T. Stützle, “Iterated robust tabu search for MAX-SAT,” in Lecture Notes in Computer Science (including subseries Lecture Notes in Artificial Intelligence and Lecture Notes in Bioinformatics), 2003, vol. 2671, pp. 129–144, doi: 10.1007/3-540-44886-1_12.
[2] E. Taillard, “Robust taboo search for the quadratic assignment problem,” Parallel Comput., vol. 17, no. 4–5, pp. 443–455, 1991, doi: 10.1016/S0167-8191(05)80147-4.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class RoTS(Base_Solver):

    def __init__(self, input_cnf_file, verbose):
        super(RoTS, self).__init__(input_cnf_file, verbose)
        '''
        Instead of using a circular list, use a list for tracking last move of each variable
        If current_time - last_move < tabu_tenure => a tabu move ! 
        Else => non-tabu moves
        Initialize all by -1
        '''
        self.tabu_tenure = int(self.nvars/10 + 4)
        self.tabu_tenure_MIN = int(self.nvars/10)
        self.tabu_tenure_MAX = int(self.nvars/10) * 3
        self.last_move = [-1 for _ in self.assignment]
        self.best_cost = len(self.list_clauses)
        self.CHECK_FREQ = self.nvars * 10
    
    def pick_allowed_lits(self,id_unsat_clauses, tabu=True):
        all_allowed_lits = []
        non_allowed_lits = []
        for ind in id_unsat_clauses:
            all_allowed_lits += self.list_clauses[ind]   
        all_allowed_lits = list(set(all_allowed_lits))
        if tabu:
            for lit in all_allowed_lits:
                if self.nb_flips - self.last_move[abs(lit)-1] < self.tabu_tenure: #tabu move
                    all_allowed_lits.remove(lit)
                    non_allowed_lits.append(lit)
        return all_allowed_lits, non_allowed_lits

    def pick_necessary_flip(self):
        oldest_move = min(self.last_move)
        if self.nb_flips - oldest_move > self.CHECK_FREQ:
            return self.assignment[self.last_move.index(oldest_move)]
        else: 
            return None 

    def solve(self):
        initial =  time.time()
        self.initialize_pool()
        while self.nb_tries < self.MAX_TRIES and not self.is_sat:
            self.generate()
            self.initialize_cost()
            self.last_move = [-1 for _ in self.assignment]
            self.best_cost = len(self.id_unsat_clauses)
            self.tabu_tenure = int(self.nvars/10 + 4)
            ''' 
            RoTS mechanism within MAX_FLIPS
            ''' 
            while self.nb_flips < self.MAX_FLIPS and not self.check():
                assert len(self.id_unsat_clauses) > 0 
                '''
                - GSAT idea (Intensification => focus on best var)
                - Among all variables that occur in unsat clauses
                - Choose a variable x which minimizes cost to flip
                '''
                # compute allowed literals wrt tabu list
                all_allowed_lits, non_allowed_lits = self.pick_allowed_lits(self.id_unsat_clauses, tabu=True)
                if len(all_allowed_lits) == 0: # else take all_allowed_lits and ignore tabu
                    all_allowed_lits, non_allowed_lits = self.pick_allowed_lits(self.id_unsat_clauses, tabu=False)
                '''
                Compute cost of every (tabu and non tabu) moves
                Cost = break - make
                '''
                ntb_cost, tb_cost = [], []
                current_cost = len(self.id_unsat_clauses)
                for literal in all_allowed_lits:
                    ntb_cost.append(self.evaluate_breakcount(literal, bs=1, ms=1))
                x_ntb = all_allowed_lits[np.argmin(ntb_cost)]
                for literal in non_allowed_lits:
                    tb_cost.append(self.evaluate_breakcount(literal, bs=1, ms=1))
                if len(tb_cost) > 0:
                    x_tb = non_allowed_lits[np.argmin(tb_cost)]
                    if min(tb_cost) < min(ntb_cost) and current_cost + min(tb_cost) < self.best_cost: #EXCEPTION
                        x = x_tb
                    else:
                        x = x_ntb
                else:
                    x = x_ntb
                
                self.flip(x) 
                self.last_move[abs(x)-1] = self.nb_flips
                if len(self.id_unsat_clauses) < self.best_cost:
                    self.best_cost = len(self.id_unsat_clauses)
                '''
                Every 10n iterations, if a variable is not flipped within 10n iterations 
                => force X to be flipped !
                '''
                if self.nb_flips % self.CHECK_FREQ == 0:
                    x = self.pick_necessary_flip()
                    if x is not None: 
                        self.flip(x)
                        self.last_move[abs(x)-1] = self.nb_flips
                        if len(self.id_unsat_clauses) < self.best_cost:
                            self.best_cost = len(self.id_unsat_clauses)
                '''
                Every n iterations => change randomly tabu tenure
                '''
                if self.nb_flips % self.nvars == 0:
                    self.tabu_tenure = random.randint(self.tabu_tenure_MIN, self.tabu_tenure_MAX)
            if self.check():
                self.is_sat = True

        end = time.time()
        print('Nb flips:  {0}      '.format(self.nb_flips))
        print('Nb tries:  {0}      '.format(self.nb_tries))
        print('CPU time:  {0:10.4f} s '.format(end-initial))
        if self.check():
            print('SAT')
            return self.assignment
        else:
            print('UNKNOWN')
            return None

    
