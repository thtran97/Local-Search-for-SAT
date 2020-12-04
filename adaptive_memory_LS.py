'''
References
[1] Z. Lü and J.-K. K. Hao, “Adaptive Memory-Based Local Search for MAX-SAT,” Elsevier, Aug. 2012. doi: 10.1016/j.asoc.2012.01.013.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class AMLS(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose):
        super(AMLS, self).__init__(input_cnf_file, verbose)
        self.initialize_pool()
        self.generate()
        self.initialize_cost()
        self.best_assignment = self.assignment.copy()
        self.best_cost = len(self.id_unsat_clauses)
        self.p = 0.0
        self.wp = 0.0
        self.last_move = [-1 for _ in self.assignment]
        self.MAX_PERT = 15
        self.MAX_FLIPS = int(self.nvars*self.nvars/4) 
        self.CHECK_FREQ = self.nvars * 10
        self.vf = [None for _ in self.list_clauses]
        self.vs = [None for _ in self.list_clauses]
        self.nf = [0 for _ in self.list_clauses]
        self.ns = [0 for _ in self.list_clauses]
        self.tabu_tenure = int(self.nvars/10 + 4)
        self.stagnation = False
        self.no_improvement_step = 0
        self.DEFINED_STEP = int(len(self.list_clauses)/6)
    
    def initialize_params(self):
        self.p = 0
        self.wp = 0 
        self.last_move = [-1 for _ in self.assignment]
        self.nb_tries += 1
        self.nb_flips = 0
        self.no_improvement_step = 0
        
    
    def update_params(self):
        if self.stagnation:
            self.no_improvement_step += 1
            if self.no_improvement_step >= self.DEFINED_STEP:
                # Increase
                self.wp += float((0.05 - self.wp)/5)
                self.p += float((1-self.p)/5)
                self.no_improvement_step = 0
        else:
            # Decrease
            self.wp -= float(self.wp/10)
            self.p -= float(self.p/10)

        nb_moves, tb_moves = self.pick_allowed_lits(self.tabu_tenure)
        nb_total_moves = len(nb_moves) + len(tb_moves)
        self.tabu_tenure = random.randint(1,10) + int(nb_total_moves*0.25)
        
        
    def pick_unsat_clause(self):
        assert len(self.id_unsat_clauses) > 0
        random_index = random.choice(self.id_unsat_clauses)
        return self.list_clauses[random_index]

    def pick_allowed_lits(self, tabu_tenure):
        allowed_lits = []
        non_allowed_lits = []
        '''
        GSAT strategy 
        '''
        for ind in self.id_unsat_clauses:
            allowed_lits += self.list_clauses[ind]   
        allowed_lits = list(set(allowed_lits))
        if tabu_tenure > 0:
            for lit in allowed_lits:
                if self.nb_flips - self.last_move[abs(lit)-1] < tabu_tenure: #tabu move
                    allowed_lits.remove(lit)
                    non_allowed_lits.append(lit)
        '''
        WalkSAT strategy
        '''
        # list_id_unsat_clauses = self.id_unsat_clauses.copy()
        # while len(allowed_lits) == 0 and len(list_id_unsat_clauses)>0:
        #     random_id = random.choice(list_id_unsat_clauses)
        #     list_id_unsat_clauses.remove(random_id)
        #     allowed_lits = self.list_clauses[random_id]
        #     if tabu_tenure > 0:
        #         for lit in allowed_lits:
        #             if self.nb_flips - self.last_move[abs(lit)-1] < tabu_tenure: #tabu move
        #                 allowed_lits.remove(lit)
        #                 non_allowed_lits.append(lit)
        return allowed_lits, non_allowed_lits


    def pick_necessary_flip(self):
        oldest_move = min(self.last_move)
        if self.nb_flips - oldest_move > self.CHECK_FREQ:
            return self.assignment[self.last_move.index(oldest_move)]
        else: 
            return None 

    def pick_1st_and_2nd_min(self, cost_list):
        assert len(cost_list) > 0
        x_1, x_2 = cost_list[0], cost_list[0]
        id_1, id_2 =  0, 0
        for i in range(1,len(cost_list)):
            if cost_list[i] <= x_1:
                x_1, x_2 = cost_list[i], x_1
                id_1, id_2 = i, id_1
            elif cost_list[i] < x_2:
                x_2 = cost_list[i]
                id_2 = i
        return id_1, id_2

    def penalty(self, y):
        list_RS, list_RF = [], []
        for i in range(len(self.list_clauses)):
            if self.vs[i] is not None and abs(self.vs[i]) == abs(y):
                list_RS.append(i)
            if self.vf[i] is not None and abs(self.vf[i]) == abs(y):
                list_RF.append(i)
        
        cost_RS, cost_RF = 0, 0
        for cs in list_RS:
            cost_RS += 2**self.ns[cs]
        for cf in list_RF:
            cost_RF += 2**self.nf[cf]
        if len(list_RS)>0:
            cost_RS = float(cost_RS/(2*len(list_RS)))
        if len(list_RF)>0:
            cost_RF = float(cost_RF/(2*len(list_RF)))
        pen = cost_RS + cost_RF
        return pen

    def pick_neighborhood(self, tabu_tenure):
        '''
        compute allowed literals wrt tabu list
        '''
        allowed_lits, non_allowed_lits = self.pick_allowed_lits(tabu_tenure)
        if len(allowed_lits) == 0: # else take allowed_lits and ignore tabu
            allowed_lits, non_allowed_lits = self.pick_allowed_lits(0)
        '''
        Compute cost of every (tabu and non tabu) moves
        Cost = break - make
        '''
        assert len(allowed_lits) > 0
        ntb_cost, tb_cost = [], []
        current_cost = len(self.id_unsat_clauses)
        for literal in allowed_lits:
            ntb_cost.append(self.evaluate_breakcount(literal, bs=1, ms=1))
        id_ntb_1st, id_ntb_2nd = self.pick_1st_and_2nd_min(ntb_cost)
        for literal in non_allowed_lits:
            tb_cost.append(self.evaluate_breakcount(literal, bs=1, ms=1))
        if len(tb_cost)>0:
            x_tb = non_allowed_lits[np.argmin(tb_cost)]
            if min(tb_cost) <  min(ntb_cost) and current_cost + min(tb_cost) < self.best_cost:
                y = x_tb
                return y

        x_nb = allowed_lits[id_ntb_1st]
        x_nsb = allowed_lits[id_ntb_2nd]

        if min(ntb_cost) < 0:
            y = x_nb
            return y

        wp = random.random()
        if wp < self.wp: 
            # Random walk on non tabu moves
            y = random.choice(allowed_lits)
            return y
        
        p = random.random()
        least_recent_move = allowed_lits[0] #largest last move
        for lit in allowed_lits[1:]:
            if self.last_move[abs(least_recent_move)-1] < self.last_move[abs(lit)-1]:
                least_recent_move = lit

        if  p < self.wp  and x_nb == least_recent_move:
            if self.penalty(x_nsb) < self.penalty(x_nb):
                y = x_nsb
                return y

        y = x_nb 
        return y

    def flip(self, literal):
        self.nb_flips += 1
        # Flip variable in assignment
        ind = 0
        if literal in self.assignment:
            ind = self.assignment.index(literal)
        elif -literal in self.assignment:
            ind = self.assignment.index(-literal) 
        old_literal = self.assignment[ind]
        self.assignment[ind] *= -1
        # Update cost
        # Clause contains literal => cost --
        if old_literal in self.pool.keys():
            for i in self.pool[old_literal]:
                self.costs[i] -= 1
                if self.costs[i] == 0: # if SAT -> UNSAT: add to list of  unsat clauses
                    self.id_unsat_clauses.append(i)
                    if self.vf[i] is not None and self.vf[i] == abs(literal):
                        self.nf[i] += 1
                    else: 
                        self.vf[i] = abs(literal)
                        self.nf[i] = 1
        # Clause contains -literal => cost ++
        if -old_literal in self.pool.keys():
            for j in self.pool[-old_literal]:
                if self.costs[j] == 0: # if UNSAT -> SAT: remove from list of unsat clauses
                    self.id_unsat_clauses.remove(j)
                    if self.vs[j] is not None and self.vs[j] == abs(literal):
                        self.ns[j] += 1
                    else: 
                        self.vs[j] = abs(literal)
                        self.ns[j] = 1
                self.costs[j] += 1

    def perturbate(self, tabu_tenure):
        nb_pert = 0
        while nb_pert < self.MAX_PERT and not self.check():
            '''
            compute allowed literals wrt tabu list
            '''
            all_allowed_lits, non_allowed_lits = self.pick_allowed_lits(tabu_tenure)
            if len(all_allowed_lits) == 0: # else take all_allowed_lits and ignore tabu
                all_allowed_lits, non_allowed_lits = self.pick_allowed_lits(0)
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
            TODO: Every n iterations => change randomly tabu tenure 
            Note: tabu tenure for perturbation phase should be larger than the one used for LS
            '''
            # if self.nb_flips % self.nvars == 0:
            #     self.tabu_tenure = random.randint(self.tabu_tenure_MIN, self.tabu_tenure_MAX)
            nb_pert += 1
        return self.assignment

    def solve(self):
        initial =  time.time()
        while self.nb_tries < self.MAX_TRIES and not self.is_sat:
            '''
            Search Phase
            '''
            self.initialize_params()
            while self.nb_flips < self.MAX_FLIPS and not self.check():
                ''' 
                Select move
                '''
                x = self.pick_neighborhood(self.tabu_tenure)
                self.flip(x) 
                '''
                Update best cost and assignment
                '''
                if len(self.id_unsat_clauses) < self.best_cost:
                    self.best_cost = len(self.id_unsat_clauses)
                    self.best_assignment = self.assignment.copy()
                    self.stagnation = False
                else: 
                    self.stagnation = True
                '''
                Add this move to the tabu list 
                Update p, wp, tabu tenure
                '''
                self.last_move[abs(x)-1] = self.nb_flips
                self.update_params()
            '''
            Perturbation Phase
            '''
            self.assignment = self.perturbate(int(self.nvars/2))
            if self.check():
                self.is_sat = True
            
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

    
