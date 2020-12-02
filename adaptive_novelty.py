'''
References
[1] D. McAllester, B. Selman, and H. Kautz, “Evidence for invariants in local search,” Proc. Natl. Conf. Artif. Intell., pp. 321–326, 1997.
[2] H. H. Hoos and T. Stützle, “Towards a characterization of the behaviour of stochastic local search algorithms for SAT,” Artif. Intell., vol. 112, no. 1, pp. 213–232, 1999, doi: 10.1016/S0004-3702(99)00048-X.
[3] H. H. Hoos, “An adaptive noise mechanism for walkSAT,” Proc. Natl. Conf. Artif. Intell., pp. 655–660, 2002.
'''

from base_solver import Base_Solver
import numpy as np
import random
import time
from itertools import chain

class Adaptive_Novelty(Base_Solver):
    
    def __init__(self, input_cnf_file, verbose, noise_parameter = 0.2):
        super(Adaptive_Novelty, self).__init__(input_cnf_file, verbose)
        self.noise_parameter = noise_parameter
        self.most_recent = None
        '''
        Introduce random walk noise parameter => Adaptive_Novelty+
        Initially set noise parameter = 0
        Then dynamically adjust noise for escaping the stagnation
        Adjustment based on parameters theta and phi
        '''
        self.random_walk_noise = 0.0
        self.THETA = float(1/6) 
        self.DEFINED_STEP = self.THETA * len(self.list_clauses)
        self.PHI = 0.2
        self.no_improvement_step = 0
        self.stagnation = False

    def solve(self):
        initial =  time.time()
        self.initialize_pool()
        while self.nb_tries < self.MAX_TRIES and not self.is_sat:
            self.generate()
            self.initialize_cost()
            self.most_recent = None
            self.no_improvement_step = 0
            self.stagnation = False
            self.random_walk_noise = 0.0
            while self.nb_flips < self.MAX_FLIPS and not self.is_sat:
                if self.check() == 1: # if no unsat clause => finish
                    self.is_sat = True
                else:
                    assert len(self.id_unsat_clauses) > 0 
                    '''
                    - [GSAT] idea (Intensification => focus on best var)
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
                    [Random walk]
                    If after DEFINED_STEP, no improvements => increase random_walk_noise
                    Over come stagnation => decrese random_walk_noise
                    '''
                    apply_novelty =  True
                    if self.stagnation:
                        # Stagnation found => count !
                        self.no_improvement_step += 1
                        if self.no_improvement_step >= self.DEFINED_STEP:
                            # Increase noise after a defined number of no-improved steps 
                            self.random_walk_noise += float((1-self.random_walk_noise) * self.PHI)
                            # Reset to check if it can overcome the stagnation within next DEFINED_STEP
                            self.no_improvement_step = 0
                    else:
                        # No stagnation => decrease noise ! 
                        self.random_walk_noise -= float(self.random_walk_noise * 2 * self.PHI)
                        self.no_improvement_step = 0
                    # Random walk to overcome stagnations 
                    if self.random_walk_noise > 0:
                        wp = random.random()
                        if wp < self.random_walk_noise:
                            x = random.choice(all_unsat_lits)
                            apply_novelty = False
                    '''
                    [Novelty strategy]
                    Arrange variables according to each cost
                    (1) If the best one *x1* is NOT the most recently flipped variable => select *x1*. 
                    Otherwise, 
                    (2a) select *x2* with probability p, 
                    (2b) select *x1* with probability 1-p.
                    '''
                    if apply_novelty:
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
                    '''
                    After choosing x, flip it and save this last recent move
                    Compare new cost with previous one => check number of no-improvement step
                    '''
                    self.current_cost = len(self.id_unsat_clauses)
                    self.flip(x) 
                    self.most_recent = abs(x)
                    if len(self.id_unsat_clauses) >= self.current_cost:
                        self.stagnation = True
                    else: 
                        self.stagnation = False

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

    
