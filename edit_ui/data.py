from util import connect_domain

def connect_domains(key, secret, prefix):
    '''
    '''
    suffixes = 'atlases', 'maps', 'rough_placements'
    domains = [connect_domain(key, secret, prefix+suffix) for suffix in suffixes]
    
    return domains
