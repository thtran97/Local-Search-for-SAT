
'''
	DIMAC parser:  read CNF file and save in a list 
    Reference: https://github.com/marcmelis/dpll-sat/blob/master/solvers/original_dpll.py 
'''
import time

def parse(filename, verbose):
    initial_time = time.time()
    clauses = []
    if verbose: 
        print('=====================[ Problem Statistics ]=====================')
        print('|                                                              |')
    for line in open(filename):
        if line.startswith('c'): continue
        if line.startswith('p'):
            nvars, nclauses = line.split()[2:4]
            if verbose:
                print('|   Nb of variables:      {0:10s}                           |'.format(nvars))
                print('|   Nb of clauses:        {0:10s}                           |'.format(nclauses))
            continue
        clause = [int(x) for x in line[:-2].split()]
        if len(clause) > 0:
            clauses.append(clause)
    
    end_time = time.time()
    if verbose:
        print('|   Parse time:      {0:10.4f}s                               |'.format(end_time - initial_time))
        print('|                                                              |')

    return clauses, int(nvars)

# # Unit test 
# cnf, maxvar = parse("cnf_instances/test.cnf")
# print(cnf, maxvar)
