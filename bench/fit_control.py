"""Ajusta familias de fórmulas de control a pares (cuerpo, control) observados."""
good=[("ALTA;Lucia",82),("ALTA;Mateo",3),("CONSULTA;AC-0001",14),("CONSULTA;AC-0002",11),
("DEPOSITO;AC-0001;250000",86),("TRANSFER;AC-0001;AC-0002;40000",86),("TRANSFER;AC-0001;AC-0002;100000",12),
("ANULA;OP-0003",66),("CONSULTA;AC-0009",87),("TRANSFER;AC-0002;AC-0001;50000",23),("DEPOSITO;AC-0002;700",35),
("CONSULTa;AC-0001",14),("CONSULTA;AC-0000",17)]
views={'full':lambda s:s,'up':lambda s:s.upper(),'args':lambda s:s.split(';',1)[1],'up_sep':lambda s:s.upper()+';',
       'args_sep':lambda s:s.split(';',1)[1]+';','up_nosemi':lambda s:s.upper().replace(';',''),'args_nosemi':lambda s:s.split(';',1)[1].replace(';','')}
for vn,v in views.items():
  for M in [97,100,101,89,83,91,99,103,127,128,256]:
    for B in range(0,M):
      for direction in ('fwd','rev'):
        def h(s):
          x=0; bs=s.encode('utf-8')
          for c in (bs if direction=='fwd' else bs[::-1]): x=(x*B+c)%M
          return x
        hs=[h(v(s)) for s,_ in good]
        for a in range(1,M):
          b=(good[0][1]-a*hs[0])%M
          if all((a*x+b)%M==c for x,(s,c) in zip(hs,good)):
            print(vn,direction,'M',M,'B',B,'a',a,'b',b)
