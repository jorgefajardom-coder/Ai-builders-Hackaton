from fit_control_data import good as g0
from collections import defaultdict
P=97
data=g0+[("CONSULTA;AC-0010",84),("CONSULTA;AC-0100",8),("CONSULTA;AC-1000",24),("CONSULTA;AD-0000",87),("CONSULTA;BC-0000",38),
 ("DEPOSITO;AC-0000;100",75),("DEPOSITO;AC-0001;100",82),("DEPOSITO;AC-0000;101",72),("DEPOSITO;AC-0000;1000",62),("DEPOSITO;AC-0001;1000",35)]
def H(s,L,low):
    h=0
    for ch in s:
        if ch.isdigit(): v=int(ch)
        elif ch.isalpha(): v=(ord(ch.upper())-65+L) if ch.isupper() or low is None else (ord(ch)-97+low)
        else: continue
        h=(h*10+v)%P
    return h
for L in range(P):
  for low in [None]+list(range(P)):
    bs=defaultdict(set)
    for s,c in data:
        cmd,args=s.split(';',1)
        bs[cmd.upper()].add((c-94*H(args,L,low))%P)
    bad=[k for k,v in bs.items() if len(v)>1]
    if len(bad)==0:
        print('L',L,'low',low,{k:min(v) for k,v in bs.items()})
