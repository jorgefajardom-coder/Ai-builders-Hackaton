from fit_control_data import good as g0
P=97
data=[x for x in g0 if not x[0].startswith(('TRANSFER','ALTA'))]+[("CONSULTA;AC-0010",84),("CONSULTA;AC-0100",8),("CONSULTA;AC-1000",24),("CONSULTA;AD-0000",87),("CONSULTA;BC-0000",38),
 ("DEPOSITO;AC-0000;100",75),("DEPOSITO;AC-0001;100",82),("DEPOSITO;AC-0000;101",72),("DEPOSITO;AC-0000;1000",62),("DEPOSITO;AC-0001;1000",35)]
test=[x for x in g0 if x[0].startswith(('TRANSFER','ALTA'))]
def H(s,L,cmd):
    if not cmd: s=s.split(';',1)[1]
    h=0
    for ch in s.upper():
        if ch.isdigit(): v=int(ch)
        elif ch.isalpha(): v=ord(ch)-65+L
        else: continue
        h=(h*10+v)%P
    return h
for cmd in (True,False):
  for L in range(P):
    hs=[H(s,L,cmd) for s,_ in data]
    a=94; b=(data[0][1]-a*hs[0])%P
    if all((a*x+b)%P==c for x,(s,c) in zip(hs,data)):
        print('fit cmd',cmd,'A=',L,'b',b, [(s,c,(a*H(s,L,cmd)+b)%P) for s,c in test])
