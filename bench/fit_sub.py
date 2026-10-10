from fit_control_data import good as g0
extra=[("CONSULTA;AC-0010",84),("CONSULTA;AC-0100",8),("CONSULTA;AC-1000",24),("CONSULTA;AD-0000",87),("CONSULTA;BC-0000",38)]
P=97
def H(s,L,semi,upper=True):
    h=0
    for ch in (s.upper() if upper else s):
        if ch.isdigit(): v=int(ch)
        elif ch.isalpha(): v=ord(ch.upper())-65+L
        elif ch==';' and semi is not None: v=semi
        else: continue
        h=(h*10+v)%P
    return h
def fit(data,label):
    hits=[]
    for vn,v in {'full':lambda s:s,'args':lambda s:s.split(';',1)[1]}.items():
      for L in range(P):
        for semi in [None]+list(range(P)):
          hs=[H(v(s),L,semi) for s,_ in data]
          i=next((i for i in range(1,len(hs)) if hs[i]!=hs[0]),None)
          if i is None: continue
          a=((data[i][1]-data[0][1])*pow((hs[i]-hs[0])%P,-1,P))%P; b=(data[0][1]-a*hs[0])%P
          if all((a*x+b)%P==c for x,(s,c) in zip(hs,data)): hits.append((vn,L,semi,a,b))
    print(label,len(hits),hits[:5])
cons=[x for x in g0+extra if x[0].upper().startswith('CONSULTA')]
fit(cons,'solo CONSULTA')
fit(cons+[x for x in g0 if x[0].startswith('DEPOSITO')],'+DEPOSITO')
fit(cons+[x for x in g0 if x[0].startswith('TRANSFER')],'+TRANSFER')
fit(cons+[x for x in g0 if x[0].startswith('ANULA')],'+ANULA')
fit(cons+[x for x in g0 if x[0].startswith('ALTA')],'+ALTA')
