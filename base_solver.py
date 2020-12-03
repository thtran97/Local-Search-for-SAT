from dimacs_parser import parse
import numpy as np
import random
import time

class Base_Solver:

    def __init__(self, input_cnf_file, verbose):
        self.list_clauses, self.nvars = parse(input_cnf_file, verbose)
        self.verbose = verbose
        self.assignment = []
        self.pool = dict() #key: literal -> element: index of clause which contains literal 
        self.id_unsat_clauses = [] # save id of unsat clause
        self.costs = np.zeros(len(self.list_clauses)) #compute nb of literals make clause true (i.e. for clause Ci, if fi>0 => T, fi==0 => F)
        self.MAX_TRIES = 50
        self.MAX_FLIPS = 100*self.nvars
        self.nb_tries = 0
        self.nb_flips = 0 
        self.is_sat = False

        for clause in self.list_clauses:
            assert len(clause) > 0

    def generate(self):
        self.assignment = []
        self.nb_tries += 1
        self.nb_flips = 0
        for x in range(1, self.nvars+1):
            choice = [-1,1]
            self.assignment.append(x * random.choice(choice))

    def initialize_pool(self): 
        for i, clause in enumerate(self.list_clauses):
            for literal in clause:
                if literal in self.pool.keys():
                    self.pool[literal].append(i)
                else:
                    self.pool[literal] = [i]

    def initialize_cost(self):
        # Compute nb of literals make clause true (i.e. for clause Ci, if fi>0 => T, fi==0 => F)
        # Let's call it cost ! 
        assert len(self.assignment) > 0
        self.id_unsat_clauses = []
        for i, clause in enumerate(self.list_clauses):
            self.costs[i] = 0
            for literal in clause:
                if literal in self.assignment:
                    self.costs[i] += 1
            if self.costs[i] == 0: #Clause[i] is currently UNSAT
                self.id_unsat_clauses.append(i)
    
    def check(self):
        # check if all is SAT 
        return len(self.id_unsat_clauses) == 0

    def evaluate_breakcount(self, literal, bs=1, ms=1):
        # Compute the breakcount score: #clause which turn SAT -> UNSAT
        ind = 0
        if literal in self.assignment:
            ind = self.assignment.index(literal)
        elif -literal in self.assignment:
            ind = self.assignment.index(-literal) 
        original_literal = self.assignment[ind]
        # when flipping literal -> -literal
        # For every clause which contains literal => cost--
        breakcount = 0
        if original_literal in self.pool.keys():
            for i in self.pool[original_literal]:
                if self.costs[i] == 1:
                    breakcount += 1
        # For every clause which contains -literal => cost ++
        makecount = 0 
        if -original_literal in self.pool.keys():
            for j in self.pool[-original_literal]:
                if self.costs[j] == 0:
                    makecount += 1
        # Score = break - make
        score = bs*breakcount - ms*makecount
        return score

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
        # Clause contains -literal => cost ++
        if -old_literal in self.pool.keys():
            for j in self.pool[-old_literal]:
                if self.costs[j] == 0: # if UNSAT -> SAT: remove from list of unsat clauses
                    self.id_unsat_clauses.remove(j)
                self.costs[j] += 1

    def solve(self):
        raise NotImplementedError