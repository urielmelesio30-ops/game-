// Tiny synthesized SFX engine (no external audio files needed).
const AudioFX = (() => {
  let ctx = null;
  function ensure() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      ctx = new AC();
    }
    if (ctx.state === 'suspended') ctx.resume();
    return ctx;
  }

  function tone(freq, dur, type, gainVal, glideTo) {
    try {
      const c = ensure();
      const osc = c.createOscillator();
      const gain = c.createGain();
      osc.type = type || 'sine';
      osc.frequency.setValueAtTime(freq, c.currentTime);
      if (glideTo) osc.frequency.exponentialRampToValueAtTime(glideTo, c.currentTime + dur);
      gain.gain.setValueAtTime(gainVal || 0.15, c.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + dur);
      osc.connect(gain).connect(c.destination);
      osc.start();
      osc.stop(c.currentTime + dur);
    } catch (e) { /* audio not available, ignore */ }
  }

  function noise(dur, gainVal) {
    try {
      const c = ensure();
      const bufferSize = c.sampleRate * dur;
      const buffer = c.createBuffer(1, bufferSize, c.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < bufferSize; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / bufferSize);
      const src = c.createBufferSource();
      src.buffer = buffer;
      const gain = c.createGain();
      gain.gain.setValueAtTime(gainVal || 0.2, c.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, c.currentTime + dur);
      src.connect(gain).connect(c.destination);
      src.start();
    } catch (e) { /* ignore */ }
  }

  return {
    unlock() { ensure(); },
    coin() { tone(1400, 0.09, 'triangle', 0.12, 2200); },
    gatePositive() { tone(400, 0.28, 'sawtooth', 0.12, 1100); },
    gateNegative() { tone(500, 0.28, 'sawtooth', 0.1, 160); },
    laser() { tone(900, 0.05, 'square', 0.03, 300); },
    hitEnemy() { noise(0.15, 0.15); tone(150, 0.15, 'sawtooth', 0.1, 60); },
    explosion() { noise(0.5, 0.3); tone(90, 0.5, 'sawtooth', 0.2, 30); },
    gameOver() { tone(300, 0.6, 'sawtooth', 0.15, 60); },
    victory() {
      tone(523, 0.15, 'triangle', 0.15);
      setTimeout(() => tone(659, 0.15, 'triangle', 0.15), 130);
      setTimeout(() => tone(784, 0.3, 'triangle', 0.18), 260);
    },
    swoosh() { noise(0.2, 0.08); }
  };
})();
