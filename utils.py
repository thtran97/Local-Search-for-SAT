import argparse

def get_args():
    argparser = argparse.ArgumentParser(description=__doc__)
    argparser.add_argument(
        '-i', '--input',
        metavar='I',
        # default='cnf_instances/Steiner-9-5-bce.cnf',
        # default='cnf_instances/Steiner-15-7-bce.cnf',
        # default='cnf_instances/Steiner-27-10-bce.cnf',
        # default='cnf_instances/test.cnf',
        default='cnf_instances/uf20-01.cnf',
        # default='cnf_instances/uf50-01.cnf',
        # default='cnf_instances/uuf50-01.cnf',
        # default='cnf_instances/uf50-06.cnf',
        # default='cnf_instances/uuf100-UNSAT.cnf',
        help='The DIMACS file')
    argparser.add_argument(
        '-v', '--verbose',
        default=1,    
        help='Verbose option')
    args = argparser.parse_args()
    return args