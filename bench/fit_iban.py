"""Hipótesis: control estilo IBAN / ISO 7064 mod 97-10 sobre el cuerpo del mensaje."""
from fit_control_data import good
def conv(s, mode):
    out=''
    for ch in s:
        if ch.isdigit(): out+=ch
        elif ch.isalpha() and ch.isascii(): out+=str(ord(ch.upper())-55)
        elif mode=='ord': out+=str(ord(ch))
        # mode 'skip': ignora separadores
    return out
views={'full':lambda s:s,'args':lambda s:s.split(';',1)[1]}
for vn,v in views.items():
  for mode in ('skip','ord'):
    for fin in ('98-x100','98-x','x','97-x'):
      ok=True; rows=[]
      for s,c in good:
        n=int(conv(v(s),mode) or '0')
        val={'98-x100':98-(n*100)%97,'98-x':98-n%97,'x':n%97,'97-x':(97-n%97)%97}[fin]
        rows.append((s,c,val)); ok&= val==c
      print(vn,mode,fin,'OK' if ok else '', [r for r in rows if r[1]!=r[2]][:3] if not ok else '')
