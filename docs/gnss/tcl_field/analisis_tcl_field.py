#!/usr/bin/env python3
"""Analisis del primer dataset real del TCL T610P.

Codigo actual verificado en useNaveGoTracker.ts:
  MAX_JUMP_DISTANCE_M = 15  (isGapRestart si haversine > 15 m, sin mirar dt ni speed)
  MIN_DISTANCE_DELTA_M = 0.8
  MIN_SPEED_FOR_COG_UPDATE = 0.3

No modifica codigo de la app. Solo lectura del JSONL.
"""
import json, math, statistics as st

PATH = 'docs/gnss/tcl_field/tcl_field_1790382982173.jsonl'
MAX_JUMP = 15.0
MIN_SPEED = 0.3

rows = [json.loads(l) for l in open(PATH) if l.strip()]
n = len(rows)

def hav(a, b):
    R = 6371e3
    p1, p2 = math.radians(a['lat']), math.radians(b['lat'])
    dp = p2 - p1
    dl = math.radians(b['lon'] - a['lon'])
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))

t0, t1 = rows[0]['measuredAt'], rows[-1]['measuredAt']
dur = (t1 - t0)/1000.0
acc = [r['accuracy'] for r in rows]
spd = [r['speed'] for r in rows]
lat = [r['measuredAt'] for r in rows]
lat_delta = [(lat[i]-lat[i-1])/1000.0 for i in range(1, n)]

print('=== ESTADISTICAS BASICAS ===')
print(f'fixes (lineas no vacias) = {n}  (la tarea declara 320)')
print(f'primer measuredAt = {t0}  ultimo = {t1}')
print(f'duracion = {dur:.1f} s = {dur/60:.2f} min')

print('\n=== dt ===')
sd = sorted(lat_delta)
print(f'dt mediano={st.median(sd):.3f}s min={min(sd):.3f}s max={max(sd):.3f}s')
print(f'dt>2s  = {sum(1 for d in sd if d>2)}')
print(f'dt>5s  = {sum(1 for d in sd if d>5)}')
print(f'dt>10s = {sum(1 for d in sd if d>10)}')
b = {'<=1.2s':0,'1.2-2s':0,'2-5s':0,'5-10s':0,'>10s':0}
for d in sd:
    if d<=1.2: b['<=1.2s']+=1
    elif d<=2: b['1.2-2s']+=1
    elif d<=5: b['2-5s']+=1
    elif d<=10: b['5-10s']+=1
    else: b['>10s']+=1
print('histograma dt:', b)

print('\n=== speed ===')
print(f'mediana={st.median(spd):.3f} max={max(spd):.3f}')
print(f'speed==0        = {sum(1 for s in spd if s==0)}')
print(f'speed>0.3 m/s   = {sum(1 for s in spd if s>0.3)}')
print(f'speed>1 m/s     = {sum(1 for s in spd if s>1)}')
print(f'speed>0 (estricto) = {sum(1 for s in spd if s>0)}')

print('\n=== accuracy ===')
print(f'mediana={st.median(acc):.3f} min={min(acc):.3f} max={max(acc):.3f}')
print(f'simulador fijo = 4.5 m ; ratio mediana/sim = {st.median(acc)/4.5:.2f}x')
print(f'acc<5m = {sum(1 for a in acc if a<5)}  acc>8m = {sum(1 for a in acc if a>8)}')

# saltos
jumps = []
for i in range(1, n):
    d = hav(rows[i-1], rows[i])
    if d > MAX_JUMP:
        jumps.append({'i': i, 't': rows[i]['measuredAt'], 'dist': d,
                      'dt': (rows[i]['measuredAt']-rows[i-1]['measuredAt'])/1000.0,
                      'speed': rows[i]['speed'], 'acc': rows[i]['accuracy']})

print('\n=== SALTOS ESPACIALES ===')
tot = sum(hav(rows[i-1], rows[i]) for i in range(1, n))
print(f'distancia acumulada cruda = {tot:.2f} m')
print(f'saltos >15m = {len(jumps)}')
for j in jumps:
    print(f"  i={j['i']} dt={j['dt']:.3f}s dist={j['dist']:.2f}m speed={j['speed']:.3f} acc={j['acc']:.2f}")

# regla propuesta: gap real si dt>2s O speed<=0.3 ; outlier si no
prop_gap = [j for j in jumps if j['dt'] > 2 or j['speed'] <= MIN_SPEED]
prop_out = [j for j in jumps if not (j['dt'] > 2 or j['speed'] <= MIN_SPEED)]
print(f'\nregla propuesta: gap_real={len(prop_gap)} outlier={len(prop_out)}')

print('\n=== FALSOS GAPS ===')
print(f'codigo actual isGapRestart = {len(jumps)}')
print(f'regla propuesta gap_real   = {len(prop_gap)}')
print(f'falsos positivos evitados  = {len(prop_out)}')

# segmentacion por tramos: detectar por velocidad/posicion
print('\n=== SEGMENTACION (movimiento por speed) ===')
segs = []
cur = None
for i, r in enumerate(rows):
    mv = r['speed'] > 0.3
    if cur is None or cur['moving'] != mv:
        if cur: segs.append(cur)
        cur = {'moving': mv, 'start': i, 'end': i}
    else:
        cur['end'] = i
if cur: segs.append(cur)
for s in segs:
    sub = rows[s['start']:s['end']+1]
    d = [(sub[k]['measuredAt']-sub[k-1]['measuredAt'])/1000.0 for k in range(1, len(sub))]
    print(f"  {'MUEVE' if s['moving'] else 'QUIETO'} idx {s['start']}-{s['end']} "
          f"n={len(sub)} dur={(sub[-1]['measuredAt']-sub[0]['measuredAt'])/1000:.0f}s "
          f"dtmed={st.median(d) if d else 0:.2f}s "
          f"accmed={st.median([x['accuracy'] for x in sub]):.2f}")
