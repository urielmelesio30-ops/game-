import json, numpy as np, wave
SR=44100; D=10.0; N=int(SR*D); rng=np.random.default_rng(7)
tl=json.load(open('timeline.json')); ev=tl['events']
out=np.zeros(N)
def add(sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig))
    if i<N: out[i:j]+=sig[:j-i]*g
def lp(x,a):  # one-pole lowpass
    y=np.zeros_like(x); s=0.0
    for i,v in enumerate(x): s+=a*(v-s); y[i]=s
    return y
def tap(f0=140,dur=.09,bright=.25):
    n=int(dur*SR); t=np.arange(n)/SR
    body=np.sin(2*np.pi*f0*t*(1-0.3*t/dur))*np.exp(-t*45)
    click=lp(rng.standard_normal(n),bright)*np.exp(-t*90)
    return body*.8+click*.9
def blip(f=1320,dur=.18):
    t=np.arange(int(dur*SR))/SR; return np.sin(2*np.pi*f*t)*np.exp(-t*18)*np.minimum(1,t*400)
def pluck(f,dur=1.6,gain=1):
    t=np.arange(int(dur*SR))/SR
    s=np.sin(2*np.pi*f*t)+.25*np.sin(2*np.pi*2*f*t)*np.exp(-t*6)+.12*np.sin(2*np.pi*5.4*f*t)*np.exp(-t*25)
    return s*np.exp(-t*2.8)*np.minimum(1,t*300)*gain
# room tone
out+=lp(rng.standard_normal(N),.02)*.03
for e in ev:
    k,t=e['kind'],e['t']
    if k=='tubehop': add(tap(120,.1,.3),t,.55)
    elif k=='tubebig': add(tap(95,.14,.35),t,.7)
    elif k=='descent': add(tap(220,.06,.5),t,.25)
    elif k=='cellhop':
        f={'rbc':260,'wbc':200,'plt':420}[e['type']]; add(tap(f*rng.uniform(.9,1.1),.05,.4),t,.18)
    elif k=='cup':
        f={'rbc':880,'wbc':740,'plt':1046}[e['type']]; add(blip(f,.12),t,.07); add(tap(300,.05,.5),t,.2)
    elif k=='blip': add(blip(1320,.2),t,.3)
    elif k=='chime':
        for i,f in enumerate([1046.5,1318.5,1568,2093]): add(pluck(f,2.0),t+i*.07,.22)
# whir while the tube goes in
ws=[e['t'] for e in ev if e['kind']=='whir_start'][0]; we=[e['t'] for e in ev if e['kind']=='whir_end'][0]+.25
n=int((we-ws)*SR); t=np.arange(n)/SR
saw=((t*170)%1-.5)+.5*((t*341)%1-.5)
wh=lp(saw,.08)*(.6+.4*np.sin(2*np.pi*11*t))*np.minimum(1,t/.08)*np.minimum(1,(n/SR-t)/.12)
add(wh,ws,.22)
# kalimba bed: 96 BPM, original pentatonic pattern
beat=60/96; notes={'C4':261.6,'D4':293.7,'E4':329.6,'G4':392.0,'A4':440.0,'C5':523.3,'D5':587.3,'E5':659.3,'G3':196.0,'A3':220.0}
pat=[('C4',0),('E4',.5),('G4',1),('A4',1.5),('G4',2),('E4',2.5),('D4',3),('E4',3.5),
     ('A3',4),('C4',4.5),('E4',5),('G4',5.5),('A4',6),('G4',6.5),('E4',7),('D4',7.5)]
music=np.zeros(N); save=out; out=music
bars=0
for rep in range(3):
    for nm,b in pat:
        t0=.2+(rep*8+b)*beat
        if t0>D: continue
        g=.35 if rep==0 else .45
        add(pluck(notes[nm],1.4),t0,g)
        if rep>=1 and b%2==0: add(pluck(notes[nm]*2,1.0),t0+.01,.12)
    if rep>=1:
        for b in [0,4]:
            t0=.2+(rep*8+b)*beat
            if t0<D: add(pluck(notes['C4']/2 if b==0 else notes['A3']/2,2.4),t0,.5)
out=save
env=np.ones(N); fo=int(.8*SR); env[-fo:]=np.linspace(1,0,fo)
mix=out+music*.32
mix*=env; mix=np.tanh(mix*1.4)/np.tanh(1.4)
mix=mix/np.max(np.abs(mix))*.85
st=np.stack([mix,mix],1)
# tiny stereo width: delay right channel 6ms on music only is overkill; keep mono-compatible
with wave.open('audio.wav','wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype(np.int16).tobytes())
print('ok')
