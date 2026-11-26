import json, numpy as np, wave
SR=44100; tl=json.load(open('timeline.json')); START=tl['START']; DUR=tl['DUR']; D=tl['TOTAL']; N=int(SR*D)
rng=np.random.default_rng(3)
def add(buf,sig,t,g=1.0):
    i=int(t*SR); j=min(N,i+len(sig))
    if 0<=i<N: buf[i:j]+=sig[:j-i]*g
def lp(x,a):
    y=np.zeros_like(x); s=0.0
    for i,v in enumerate(x): s+=a*(v-s); y[i]=s
    return y
def env(n,att=.003,dec=30): t=np.arange(n)/SR; return np.minimum(1,t/att)*np.exp(-t*dec)
def mixs(*a):
    n=max(len(x) for x in a); o=np.zeros(n)
    for x in a: o[:len(x)]+=x
    return o
def tone(f,dur,dec,att=.003): n=int(dur*SR); t=np.arange(n)/SR; return np.sin(2*np.pi*f*t)*env(n,att,dec)
def noise(dur,a,dec): n=int(dur*SR); return lp(rng.standard_normal(n),a)*env(n,.001,dec)
def pluck(f,dur=1.5):
    t=np.arange(int(dur*SR))/SR
    return (np.sin(2*np.pi*f*t)+.25*np.sin(4*np.pi*f*t)*np.exp(-t*6)+.12*np.sin(2*np.pi*5.4*f*t)*np.exp(-t*25))*np.exp(-t*2.8)*np.minimum(1,t*300)
fx=np.zeros(N); mus=np.zeros(N); vo=np.zeros(N)
fx+=lp(rng.standard_normal(N),.02)*.025
for e in tl['events']:
    k,t=e['kind'],e['t']
    if k=='tap': add(fx,mixs(tone(150,.1,40)*.7,noise(.08,.3,80)),t,.35)
    elif k=='tick': add(fx,mixs(tone(900,.04,90),noise(.03,.5,120)*.5),t,.12)
    elif k=='slurp':
        n=int(.9*SR); tt=np.arange(n)/SR; f=300+250*tt
        add(fx,np.sin(2*np.pi*np.cumsum(f)/SR)*np.minimum(1,tt/.05)*np.minimum(1,(.9-tt)/.2)*.5+lp(rng.standard_normal(n),.1)*.3,t,.18)
    elif k=='plink': add(fx,mixs(tone(1250,.25,14),tone(1870,.2,20)*.4),t,.2)
    elif k=='pulseBig': add(fx,tone(620,.07,45),t,.16)
    elif k=='pulseSmall': add(fx,tone(1240,.05,60),t,.12)
    elif k=='pop': add(fx,mixs(noise(.06,.6,70),tone(500,.05,60)*.5),t,.22)
    elif k=='scatter': add(fx,mixs(tone(1500,.12,25),tone(2250,.1,30)*.5),t,.12)
    elif k=='chime':
        for i,f in enumerate([1046.5,1318.5,1568,2093]): add(fx,pluck(f,2.0),t+i*.08,.2)
# hums: lamp (shot 4 after 6s), laser (shot 5)
def hum(t0,t1,f,g):
    n=int((t1-t0)*SR); tt=np.arange(n)/SR; s=(np.sin(2*np.pi*f*tt)+.3*np.sin(2*np.pi*2*f*tt))*np.minimum(1,tt/.15)*np.minimum(1,(t1-t0-tt)/.15); add(fx,s,t0,g)
hum(START[3]+6.0,START[3]+DUR[3],110,.05); hum(START[4]+.05,START[4]+DUR[4],180,.04)
# voice
for i in range(6):
    w=wave.open(f'../explain/vo{i+1}.wav'); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
    x=np.interp(np.arange(0,len(x)/sr,1/SR),np.arange(len(x))/sr,x); x/=np.max(np.abs(x))+1e-9
    add(vo,x,START[i]+.4,.9)
# music: soft kalimba, 92 BPM, original pattern
beat=60/92; scale=[261.6,293.7,329.6,392.0,440.0,523.3]
pat=[0,2,4,3,2,4,1,2, 0,2,3,5,4,3,1,2]
b=0
while (t:=.2+b*.5*beat)<D-1.5:
    add(mus,pluck(scale[pat[b%16]],1.3),t,.5)
    if b%8==0: add(mus,pluck(scale[pat[b%16]]/2,2.2),t,.5)
    b+=1
# duck music under voice
venv=np.convolve(np.abs(vo),np.ones(4410)/4410,'same'); duck=1-0.55*np.clip(venv*12,0,1)
mix=vo+fx+mus*.22*duck
fo=int(1.2*SR); mix[-fo:]*=np.linspace(1,0,fo)
mix=np.tanh(mix*1.3)/np.tanh(1.3); mix=mix/np.max(np.abs(mix))*.9
st=(np.stack([mix,mix],1)*32767).astype(np.int16)
with wave.open('ex_audio.wav','wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('ok',D)
