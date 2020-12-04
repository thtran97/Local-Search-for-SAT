'''
References
[1] D. McAllester, B. Selman, and H. Kautz, “Evidence for invariants in local search,” Proc. Natl. Conf. Artif. Intell., pp. 321–326, 1997.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class IRoTS(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose):
        super(IRoTS, self).__init__(input_cnf_file, verbose)
        '''
        Instead of using a circular list, use a list for tracking last move of each variable
        If current_time - last_move < tabu_tenure => a tabu move ! 
        Else => non-tabu moves
        Initialize all by -1
        '''
        self.tabu_tenure_LS = int(self.nvars/10 + 4)
        # self.tabu_tenure_LS_MIN = int(self.nvars/10)
        # self.tabu_tenure_LS_MAX = int(self.nvars/10) * 3
        self.tabu_tenure_Perturb = int(self.nvars/2)
        self.last_move = [-1 for _ in self.assignment]
        self.best_cost = len(self.list_clauses)
        self.CHECK_FREQ = self.nvars * 10
        self.nb_no_improvements = 0
        self.ESCAPE_THRESHOLD = int(self.nvars*self.nvars/4)
        self.nb_perturbations = 0
        self.MAX_PERTURBATIONS = int(9*self.nvars/10)

    def pick_allowed_lits(self,id_unsat_clauses, tabu_tenure):
        all_allowed_lits = []
        non_allowed_lits = []
        for ind in id_unsat_clauses:
            all_allowed_lits += self.list_clauses[ind]   
        all_allowed_lits = list(set(all_allowed_lits))
        if tabu_tenure > 0:
            for lit in all_allowed_lits:
                if self.nb_flips - self.last_move[abs(lit)-1] < tabu_tenure: #tabu move
                    all_allowed_lits.remove(lit)
                    non_allowed_lits.append(lit)
        return all_allowed_lits, non_allowed_lits

    def pick_necessary_flip(self):
        oldest_move = min(self.last_move)
        if self.nb_flips - oldest_move > self.CHECK_FREQ:
            return self.assignment[self.last_move.index(oldest_move)]
        else: 
            return None 

    def RoTS(self, mode_LS=False, mode_Perturbation=False):
        condition = False
        self.nb_perturbations = 0
        self.nb_no_improvements = 0
        if mode_LS:
            condition =  self.nb_no_improvements < self.ESCAPE_THRESHOLD
            tabu_tenure = self.tabu_tenure_LS
        elif mode_Perturbation:
            condition =  self.nb_perturbations < self.MAX_PERTURBATIONS
            tabu_tenure = self.tabu_tenure_Perturb
        
        while condition and self.nb_flips < self.MAX_FLIPS and not self.check() :
            '''
            compute allowed literals wrt tabu list
            '''
            all_allowed_lits, non_allowed_lits = self.pick_allowed_lits(self.id_unsat_clauses, tabu_tenure)
            if len(all_allowed_lits) == 0: # else take all_allowed_lits and ignore tabu
                all_allowed_lits, non_allowed_lits = self.pick_allowed_lits(self.id_unsat_clauses, 0)
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
                self.nb_no_improvements = 0
            else: 
                self.nb_no_improvements += 1
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
                        self.nb_no_improvements = 0
                    else:
                        self.nb_no_improvements += 1
            '''
            TODO: Every n iterations => change randomly tabu tenure 
            Note: tabu tenure for perturbation phase should be larger than the one used for LS
            '''
            # if self.nb_flips % self.nvars == 0:
            #     self.tabu_tenure = random.randint(self.tabu_tenure_MIN, self.tabu_tenure_MAX)
            self.nb_perturbations += 1
            if mode_LS:
                condition =  self.nb_no_improvements < self.ESCAPE_THRESHOLD
            elif mode_Perturbation:
                condition =  self.nb_perturbations < self.MAX_PERTURBATIONS
        return self.check()

    def solve(self):
        initial =  time.time()
        self.initialize_pool()        
        while self.nb_tries < self.MAX_TRIES and not self.is_sat:
            ''' 
            Random assignment & parameter initialization
            '''
            self.generate()
            self.initialize_cost()
            self.last_move = [-1 for _ in self.assignment]
            self.best_cost = len(self.id_unsat_clauses)
            # self.tabu_tenure_LS = int(self.nvars/10 + 4)
            # self.tabu_tenure_Perturb = int(self.nvars/2)
            '''
            LS
            '''
            self.is_sat = self.RoTS(mode_LS=True)
            while not self.is_sat and self.nb_flips < self.MAX_FLIPS:
                '''
                Pertubation Operator
                '''
                x_star = self.assignment.copy()
                x_star_cost = len(self.id_unsat_clauses)
                self.last_move = [-1 for _ in self.assignment]
                self.is_sat = self.RoTS(mode_Perturbation=True)
                '''
                LS
                '''
                xp_star = self.assignment.copy()
                xp_star_cost = len(self.id_unsat_clauses)
                self.last_move = [-1 for _ in self.assignment]
                if not self.is_sat:
                    self.is_sat = self.RoTS(mode_LS=True)
                    xp_star = self.assignment.copy()
                    xp_star_cost = len(self.id_unsat_clauses)
                '''
                Acceptance Criterion
                '''
                if xp_star_cost < self.best_cost:
                    self.best_cost = xp_star_cost
                    self.assignment = xp_star
                else:
                    p = random.random() 
                    if xp_star_cost == x_star_cost: 
                        if p < 0.5:
                            self.assignment = xp_star
                        else:
                            self.assignment = x_star
                    elif xp_star_cost > x_star_cost:
                        if p < 0.1:
                            self.assignment = x_star
                        else:
                            self.assignment = xp_star
                    elif xp_star_cost < x_star_cost:
                        if p < 0.1:
                            self.assignment = xp_star
                        else:
                            self.assignment = x_star
                self.initialize_cost()
                

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

    
