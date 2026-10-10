from fit_control_data import good
good = good + [("CONSULTA;AC-0010",84),("CONSULTA;AC-0100",8),("CONSULTA;AC-1000",24),
               ("CONSULTA;AD-0000",87),("CONSULTA;BC-0000",38)]
P=97
def H(s, L, semi, dash, B):
    h=0
    for ch in s.upper():
        if ch.isdigit(): v=int(ch)
        elif ch.isalpha(): v=ord(ch)-65+L
        elif ch==';':
            if semi is None: continue
            v=semi
        elif ch=='-':
            if dash is None: continue
            v=dash
        else: continue
        h=(h*B+v)%P
    return h
views={'full':lambda s:s,'args':lambda s:s.split(';',1)[1]}
for vn,v in views.items():
 for B in (10,):
  for L in range(0,P):
    for semi in [None]+list(range(P)):
      for dash in (None,):
        hs=[H(v(s),L,semi,dash,B) for s,_ in good]
        # resolver a con dos puntos de h distinto
        i=next((i for i in range(1,len(hs)) if hs[i]!=hs[0]),None)
        if i is None: continue
        inv=pow((hs[i]-hs[0])%P,-1,P)
        a=((good[i][1]-good[0][1])*inv)%P
        b=(good[0][1]-a*hs[0])%P
        if all((a*x+b)%P==c for x,(s,c) in zip(hs,good)):
            print('MATCH',vn,'B',B,'A=',L,'semi',semi,'dash',dash,'a',a,'b',b)
