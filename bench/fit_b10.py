"""Hipótesis: h = h*10 + v(c) mod 97 sobre caracteres alfanuméricos; control = a*h + b mod 97."""
from fit_control_data import good
good = good + [("CONSULTA;AC-0010",84),("CONSULTA;AC-0100",8),("CONSULTA;AC-1000",24),
               ("CONSULTA;AD-0000",87),("CONSULTA;BC-0000",38)]
def H(s, L, keep, upper):
    h=0
    for ch in (s.upper() if upper else s):
        if ch.isdigit(): v=int(ch)
        elif ch.isalpha(): v=ord(ch.upper())-65+L
        elif ch in keep: v=keep[ch]
        else: continue
        h=(h*10+v)%97
    return h
views={'full':lambda s:s,'args':lambda s:s.split(';',1)[1]}
for vn,v in views.items():
  for upper in (True,False):
    for L in range(0,97):
      for kn,keep in (('skip',{}),):
        hs=[H(v(s),L,keep,upper) for s,_ in good]
        for a in range(1,97):
          b=(good[0][1]-a*hs[0])%97
          if all((a*x+b)%97==c for x,(s,c) in zip(hs,good)):
            print('MATCH',vn,'upper',upper,'A=',L,kn,'a',a,'b',b)
