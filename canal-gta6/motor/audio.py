# -*- coding: utf-8 -*-
"""Voz (Kokoro TTS, local) y música/efectos originales generados por código.

La voz se procesa después en ffmpeg (CADENA_VOZ): tono un pelín más alto y
amable, agudos suavizados y compresión ligera (estilo narración de TikTok)."""
import hashlib, os, re
import numpy as np
import soundfile as sf
from scipy.signal import lfilter, butter

VOZ_SR = 24000
MUS_SR = 48000
MODELO = os.environ.get("KOKORO_MODEL", "/opt/tts/kokoro-v1.0.onnx")
VOCES = os.environ.get("KOKORO_VOICES", "/opt/tts/voices-v1.0.bin")
VOZ = os.environ.get("VOZ", "ef_dora")
VELOCIDAD = float(os.environ.get("VELOCIDAD", "1.0"))
CADENA_VOZ = os.environ.get("CADENA_VOZ", (
    "rubberband=pitch=1.03:formant=preserved,highpass=f=80,equalizer=f=250:t=q:w=1:g=1.5,"
    "equalizer=f=2500:t=q:w=1.2:g=1.5,highshelf=f=7000:g=-3,"
    "acompressor=threshold=0.1:ratio=2.5:attack=10:release=180:makeup=1.5"))
CACHE = os.path.join(os.path.dirname(__file__), "..", ".cache_voz")

# Pronunciación: el TTS lee con fonética española, así que los nombres en
# inglés se escriben "como suenan". Orden: de más largo a más corto.
PRONUNCIA = [
    ("GTA Online 2", "ge te a onlain dos"), ("GTA Online", "ge te a onlain"),
    ("GTA+", "ge te a plus"), ("GTA 6", "ge te a seis"), ("GTA 5", "ge te a cinco"),
    ("GTA 2", "ge te a dos"), ("GTA III", "ge te a tres"), ("GTA IV", "ge te a cuatro"),
    ("GTA", "ge te a"),
    ("Red Dead Redemption 2", "Red Ded Ridémshon dos"),
    ("PlayStation Store", "Pleisteishon Stor"), ("PlayStation Plus", "Pleisteishon Plas"),
    ("PlayStation", "Pleisteishon"), ("Microsoft Store", "Máicrosoft Stor"),
    ("Xbox Series X y S", "Equisbox Siries equis y ese"), ("Xbox Series", "Equisbox Siries"),
    ("Xbox Game Pass", "Equisbox Geim Pas"), ("Xbox", "Equisbox"),
    ("Rockstar North", "Rokstar Nort"), ("Rockstar", "Rokstar"), ("Take-Two", "Teik Tu"),
    ("DMA Design", "de eme a Disáin"),
    ("Leonida Keys", "Leonida Kis"), ("Grassrivers", "Grasríverss"), ("Port Gellhorn", "Port Guéljorn"),
    ("Mount Kalaga", "Maunt Kalaga"), ("Vice City", "Váis Síti"), ("Liberty City", "Líberti Síti"),
    ("Everglades", "Évergleids"), ("Vintage", "Víntach"),
    ("Dre'Quan Priest", "Dre Kuan Prist"), ("Boobie Ike", "Búbi Áik"), ("Cal Hampton", "Cal Jámpton"),
    ("Brian Heder", "Bráian Jéder"), ("Real Dimez", "Ríal Dáims"), ("Tommy Vercetti", "Tómi Verchéti"),
    ("Carl Johnson", "Carl Yónson"), ("Niko Bellic", "Níko Bélik"),
    ("Michael, Franklin y Trevor", "Máikol, Fránklin y Trévor"),
    ("Jason Duval", "Yéison Duval"), ("Jason", "Yéison"),
    ("Ultimate", "Áltimet"), ("YouTube", "Yutub"), ("Windows", "Uíndous"),
    ("PCIe 4.0", "pe ce i e cuatro punto cero"), ("M punto 2", "eme punto dos"),
    ("SSD", "ese ese de"), ("APK", "a pe ka"), ("USB", "u ese be"), ("PC", "pe ce"),
    ("Zona 6", "Zona seis"), ("online", "onlain"), ("like", "láik"), ("streamer", "estrímer"),
    ("Slim", "Slim"), ("Pro", "Pro"),
]


def pronunciar(texto):
    t = texto
    for a, b in PRONUNCIA:
        t = re.sub(r"(?<![\wÁÉÍÓÚáéíóúñ])" + re.escape(a) + r"(?![\wÁÉÍÓÚáéíóúñ])", b, t)
    return t


_kokoro = None


def voz(texto):
    """Devuelve audio float32 mono a 24 kHz. Cachea por texto+voz."""
    global _kokoro
    os.makedirs(CACHE, exist_ok=True)
    dicho = pronunciar(texto)
    h = hashlib.sha1(f"{VOZ}|{VELOCIDAD}|{dicho}".encode()).hexdigest()[:16]
    ruta = os.path.join(CACHE, h + ".wav")
    if os.path.exists(ruta):
        a, _ = sf.read(ruta, dtype="float32")
        return a
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(MODELO, VOCES)
    a, sr = _kokoro.create(dicho, voice=VOZ, speed=VELOCIDAD, lang="es")
    assert sr == VOZ_SR
    a = a.astype(np.float32)
    # recorta silencios de los extremos
    nz = np.where(np.abs(a) > 0.01)[0]
    if len(nz):
        a = a[max(0, nz[0] - 600): nz[-1] + 1800]
    sf.write(ruta, a, VOZ_SR)
    return a


# --------------------------------------------------------------------------
# Música synthwave original, generada nota a nota (sin samples de terceros).
# --------------------------------------------------------------------------
NOTAS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def _lp(x, fc, sr=MUS_SR, orden=2):
    b, a = butter(orden, fc / (sr / 2), "low")
    return lfilter(b, a, x)


def _hp(x, fc, sr=MUS_SR, orden=2):
    b, a = butter(orden, fc / (sr / 2), "high")
    return lfilter(b, a, x)


def _saw(f, n, sr=MUS_SR, det=0.0):
    t = np.arange(n) / sr
    return 2 * ((t * f * (1 + det)) % 1.0) - 1


def _env(n, a, r, sr=MUS_SR):
    e = np.ones(n)
    na, nr = int(a * sr), int(r * sr)
    if na: e[:na] = np.linspace(0, 1, na)
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e


def musica(segundos, semilla=0, bpm=100, tono="A"):
    rng = np.random.default_rng(semilla)
    sr = MUS_SR
    beat = 60 / bpm
    compas = 4 * beat
    raiz = 45 + NOTAS[tono]  # La2 aprox
    # progresión menor i - VI - III - VII (dos compases por acorde)
    grados = [(0, [0, 3, 7]), (-4, [0, 4, 7]), (3, [0, 4, 7]), (-2, [0, 4, 7])]
    if semilla % 2:
        grados = [(0, [0, 3, 7]), (-2, [0, 4, 7]), (-4, [0, 4, 7]), (-5, [0, 3, 7])]
    n_loop = int(8 * compas * sr)
    L = np.zeros(n_loop)
    R = np.zeros(n_loop)

    def add(buf, sig, t0):
        i = int(t0 * sr)
        j = min(len(buf), i + len(sig))
        if i < len(buf):
            buf[i:j] += sig[: j - i]

    for k, (g, tri) in enumerate(grados):
        t_acorde = k * 2 * compas
        dur = 2 * compas
        n = int(dur * sr)
        # pad
        pad = np.zeros(n)
        for iv in tri:
            f = hz(raiz + 12 + g + iv)
            pad += _saw(f, n, det=0.003) + _saw(f, n, det=-0.004)
        pad = _lp(pad, 1400) * _env(n, 0.6, 0.6) * 0.05
        add(L, pad, t_acorde); add(R, pad * 0.9, t_acorde)
        # bajo en corcheas
        for c in range(16):
            nb = int(beat / 2 * sr)
            fb = hz(raiz - 12 + g + (12 if c % 4 == 3 else 0))
            b = _lp(_saw(fb, nb), 500) * _env(nb, 0.005, 0.08) * 0.22
            add(L, b, t_acorde + c * beat / 2); add(R, b, t_acorde + c * beat / 2)
        # arpegio en semicorcheas
        patron = [0, 1, 2, 1, 2, 0, 1, 2]
        for c in range(32):
            na_ = int(beat / 4 * sr)
            iv = tri[patron[c % 8]] + (12 if (c // 8) % 2 else 0)
            fa = hz(raiz + 24 + g + iv)
            t = np.arange(na_) / sr
            sq = np.sign(np.sin(2 * np.pi * fa * t)) * 0.5 + np.sin(2 * np.pi * fa * t) * 0.5
            s = _lp(sq, 2500) * np.exp(-t * 18) * 0.06
            pan = 0.5 + 0.35 * np.sin(c)
            add(L, s * (1 - pan) * 2, t_acorde + c * beat / 4)
            add(R, s * pan * 2, t_acorde + c * beat / 4)
    # batería
    nk = int(0.35 * sr)
    tk = np.arange(nk) / sr
    kick = np.sin(2 * np.pi * (50 * tk + 90 * (1 - np.exp(-tk * 30)) / 30)) * np.exp(-tk * 9) * 0.55
    ns = int(0.25 * sr)
    ts = np.arange(ns) / sr
    snare = (_hp(rng.standard_normal(ns), 1200) * 0.35 + np.sin(2 * np.pi * 190 * ts) * 0.3) * np.exp(-ts * 16) * 0.35
    nh = int(0.06 * sr)
    hat = _hp(rng.standard_normal(nh), 7000) * np.exp(-np.arange(nh) / sr * 60) * 0.12
    for b_ in range(32):
        t0 = b_ * beat
        add(L, kick, t0); add(R, kick, t0)
        if b_ % 2 == 1:
            add(L, snare, t0); add(R, snare, t0)
        for h_ in range(2):
            add(L, hat * 0.8, t0 + h_ * beat / 2); add(R, hat, t0 + h_ * beat / 2)
    # eco sencillo para dar aire
    d = int(beat * 0.75 * sr)
    L[d:] += R[:-d] * 0.18
    R[d:] += L[:-d] * 0.18
    loop = np.stack([L, R], 1)
    total = int(segundos * sr)
    reps = total // n_loop + 1
    pista = np.tile(loop, (reps, 1))[:total]
    # entrada y salida
    fi, fo = int(2 * sr), int(3 * sr)
    pista[:fi] *= np.linspace(0, 1, fi)[:, None]
    pista[-fo:] *= np.linspace(1, 0, fo)[:, None]
    pista /= max(1e-6, np.abs(pista).max())
    return pista.astype(np.float32) * 0.8


def whoosh(semilla=0):
    rng = np.random.default_rng(1000 + semilla)
    n = int(0.55 * MUS_SR)
    t = np.linspace(0, 1, n)
    ruido = rng.standard_normal(n)
    # barrido de filtro: mezcla de pasa-bajos con corte creciente
    a = _lp(ruido, 600) * (1 - t) + _lp(ruido, 4000) * t
    env = np.sin(np.pi * t) ** 2
    s = a * env
    s /= np.abs(s).max()
    return np.stack([s * (0.6 + 0.4 * t), s * (1 - 0.4 * t)], 1).astype(np.float32) * 0.5


# --------------------------------------------------------------------------
# Chiptune (estilo consola de 8 bits): pulsos, triángulo y ruido.
# --------------------------------------------------------------------------
def _pulso(f, n, duty=0.25, sr=MUS_SR):
    t = np.arange(n) / sr
    return np.where((t * f) % 1.0 < duty, 1.0, -1.0)


def _triangulo(f, n, sr=MUS_SR):
    t = np.arange(n) / sr
    x = (t * f) % 1.0
    # triángulo cuantizado a 16 niveles, como el canal de triángulo clásico
    tri = 4 * np.abs(x - 0.5) - 1
    return np.round(tri * 8) / 8


def _ruido(n, rng, periodo=1):
    r = rng.choice([-1.0, 1.0], size=n // periodo + 1)
    return np.repeat(r, periodo)[:n]


def chiptune(segundos, semilla=0, bpm=120, tono="A"):
    rng = np.random.default_rng(semilla)
    sr = MUS_SR
    beat = 60 / bpm
    paso = beat / 4  # semicorchea
    raiz = 57 + NOTAS[tono] - 9  # La3 aprox
    progs = [
        [(0, [0, 3, 7]), (-4, [0, 4, 7]), (3, [0, 4, 7]), (-2, [0, 4, 7])],
        [(0, [0, 3, 7]), (-2, [0, 4, 7]), (-4, [0, 4, 7]), (-5, [0, 3, 7])],
        [(0, [0, 3, 7]), (5, [0, 3, 7]), (-4, [0, 4, 7]), (-2, [0, 4, 7])],
    ]
    prog = progs[semilla % 3]
    n_loop = int(64 * paso * sr) * 2  # 8 compases
    L = np.zeros(n_loop)

    def add(sig, t0):
        i = int(t0 * sr)
        j = min(len(L), i + len(sig))
        if i < len(L):
            L[i:j] += sig[: j - i]

    patrones = [[0, 1, 2, 1, 2, 0, 1, 2], [0, 2, 1, 2, 0, 2, 1, 2], [0, 1, 2, 3, 2, 1, 0, 1]]
    pat = patrones[semilla % 3]
    for k, (g, tri) in enumerate(prog):
        t_ac = k * 32 * paso
        acorde = tri + [12]
        for c in range(32):
            # arpegio (pulso 12,5 %)
            nota = raiz + 12 + g + acorde[pat[c % 8] % len(acorde)]
            n = int(paso * sr * 0.9)
            env = np.linspace(1, 0.35, n)
            add(_pulso(hz(nota), n, 0.125) * env * 0.045, t_ac + c * paso)
            # bajo en triángulo (corcheas)
            if c % 2 == 0:
                nb = int(paso * 2 * sr * 0.85)
                fb = hz(raiz - 12 + g + (12 if c % 8 == 6 else 0))
                add(_triangulo(fb, nb) * 0.16, t_ac + c * paso)
        # melodía simple (pulso 50 %) en negras, solo en la segunda vuelta
        for b in range(8):
            if (b + k) % 3 == 2:
                continue
            nm = int(beat * sr * 0.8)
            nota = raiz + 24 + g + tri[(b * 2 + k) % 3]
            env = np.exp(-np.arange(nm) / sr * 3)
            add(_pulso(hz(nota), nm, 0.5) * env * 0.03, t_ac + 32 * paso * 0 + b * beat + 0.0)
    # batería de 8 bits
    for b in range(32):
        t0 = b * beat
        nk = int(0.12 * sr)
        tk = np.arange(nk) / sr
        fk = 180 * np.exp(-tk * 30) + 40
        kick = np.round(np.sin(2 * np.pi * np.cumsum(fk) / sr) * 4) / 4 * np.exp(-tk * 20) * 0.35
        add(kick, t0)
        if b % 2 == 1:
            ns = int(0.14 * sr)
            add(_ruido(ns, rng, 3) * np.exp(-np.arange(ns) / sr * 22) * 0.12, t0)
        for h in range(2):
            nh = int(0.03 * sr)
            add(_ruido(nh, rng, 1) * np.exp(-np.arange(nh) / sr * 90) * 0.05, t0 + h * beat / 2)
    loop = np.stack([L, L], 1)
    # un poco de eco estéreo para que no suene plano
    d = int(paso * 3 * sr)
    loop[d:, 1] += loop[:-d, 0] * 0.25
    total = int(segundos * sr)
    pista = np.tile(loop, (total // len(loop) + 1, 1))[:total]
    fi, fo = int(1.0 * sr), int(2.5 * sr)
    pista[:fi] *= np.linspace(0, 1, fi)[:, None]
    pista[-fo:] *= np.linspace(1, 0, fo)[:, None]
    pista /= max(1e-6, np.abs(pista).max())
    return pista.astype(np.float32) * 0.8


def blip(tipo=0):
    """Efecto 8-bit corto: 0 = aparece un elemento, 1 = transición, 2 = moneda."""
    sr = MUS_SR
    if tipo == 0:
        n = int(0.07 * sr)
        f = np.where(np.arange(n) < n // 2, 988, 1319)
        s = np.where((np.cumsum(f) / sr) % 1.0 < 0.5, 1.0, -1.0) * np.linspace(1, 0.2, n) * 0.22
    elif tipo == 1:
        n = int(0.28 * sr)
        rng = np.random.default_rng(5)
        per = np.linspace(1, 14, n).astype(int)
        r = rng.choice([-1.0, 1.0], size=n)
        s = np.array([r[i - i % p] for i, p in enumerate(per)]) * np.linspace(1, 0, n) ** 1.5 * 0.18
    else:
        n = int(0.22 * sr)
        f = np.where(np.arange(n) < int(0.06 * sr), 988, 1976)
        s = np.where((np.cumsum(f) / sr) % 1.0 < 0.5, 1.0, -1.0) * np.exp(-np.arange(n) / sr * 9) * 0.2
    return np.stack([s, s], 1).astype(np.float32)
