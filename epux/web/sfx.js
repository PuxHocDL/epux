/* EPux SFX — âm thanh tổng hợp bằng Web Audio API, không cần file audio.
   Tông "chuông pha lê" fantasy: hợp âm trưởng, triangle/sine, noise lọc dải. */
"use strict";

const SFX = (() => {
  let ctx = null;
  let master = null;
  let enabled = localStorage.getItem("epux-sfx") !== "off";

  function ensure() {
    if (!ctx) {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
      master = ctx.createGain();
      master.gain.value = 0.35;
      master.connect(ctx.destination);
    }
    if (ctx.state === "suspended") ctx.resume();
    return ctx;
  }

  function tone({ f = 440, f2 = null, type = "sine", t = 0, dur = 0.15, vol = 1, attack = 0.005 }) {
    const c = ensure();
    const now = c.currentTime + t;
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(f, now);
    if (f2) osc.frequency.exponentialRampToValueAtTime(Math.max(30, f2), now + dur);
    g.gain.setValueAtTime(0, now);
    g.gain.linearRampToValueAtTime(vol, now + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    osc.connect(g);
    g.connect(master);
    osc.start(now);
    osc.stop(now + dur + 0.05);
  }

  function noise({ t = 0, dur = 0.2, vol = 0.4, from = 400, to = 2000, filter = "bandpass", q = 1 }) {
    const c = ensure();
    const now = c.currentTime + t;
    const len = Math.max(1, Math.floor(c.sampleRate * dur));
    const buf = c.createBuffer(1, len, c.sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
    const src = c.createBufferSource();
    src.buffer = buf;
    const filt = c.createBiquadFilter();
    filt.type = filter;
    filt.Q.value = q;
    filt.frequency.setValueAtTime(from, now);
    filt.frequency.exponentialRampToValueAtTime(Math.max(40, to), now + dur);
    const g = c.createGain();
    g.gain.setValueAtTime(vol, now);
    g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    src.connect(filt);
    filt.connect(g);
    g.connect(master);
    src.start(now);
  }

  const sounds = {
    // UI
    click() { tone({ f: 700, type: "triangle", dur: 0.06, vol: 0.22 }); },
    ok() { tone({ f: 880, type: "triangle", dur: 0.1, vol: 0.18 }); },
    err() { tone({ f: 190, f2: 140, type: "sine", dur: 0.2, vol: 0.28 }); },

    // Ôn tập
    flip() {
      noise({ dur: 0.16, vol: 0.28, from: 600, to: 2600 });
      tone({ f: 480, f2: 720, dur: 0.12, vol: 0.18, t: 0.03 });
    },
    rate0() { tone({ f: 200, f2: 130, dur: 0.28, vol: 0.45 }); },
    rate1() { tone({ f: 330, dur: 0.12, vol: 0.35 }); },
    rate2() { tone({ f: 523, dur: 0.1, vol: 0.32 }); tone({ f: 659, t: 0.09, dur: 0.16, vol: 0.32 }); },
    rate3() { [523, 659, 784].forEach((f, i) => tone({ f, type: "triangle", t: i * 0.07, dur: 0.14, vol: 0.32 })); },

    // Quiz
    correct() { [523, 659, 784, 1047].forEach((f, i) => tone({ f, type: "triangle", t: i * 0.08, dur: 0.2, vol: 0.38 })); },
    wrong() {
      tone({ f: 240, f2: 150, type: "sawtooth", dur: 0.3, vol: 0.2 });
      tone({ f: 120, f2: 85, dur: 0.32, vol: 0.3, t: 0.02 });
    },

    // Gacha
    claim() {
      [659, 784, 988].forEach((f, i) => tone({ f, type: "triangle", t: i * 0.09, dur: 0.22, vol: 0.38 }));
      noise({ t: 0.26, dur: 0.3, vol: 0.1, from: 3000, to: 7000 });
    },
    shake() { noise({ dur: 0.95, vol: 0.3, from: 140, to: 60, filter: "lowpass" }); },
    burst() {
      noise({ dur: 0.5, vol: 0.38, from: 300, to: 6000 });
      tone({ f: 880, f2: 1760, type: "triangle", dur: 0.4, vol: 0.26 });
    },
    revealCommon() { [523, 784].forEach((f, i) => tone({ f, type: "triangle", t: i * 0.1, dur: 0.28, vol: 0.38 })); },
    revealRare() {
      [523, 659, 784, 1047].forEach((f, i) => tone({ f, type: "triangle", t: i * 0.1, dur: 0.32, vol: 0.38 }));
      tone({ f: 131, dur: 0.55, vol: 0.24 });
    },
    revealEpic() {
      [392, 523, 659, 784, 1047, 1319].forEach((f, i) => tone({ f, type: "triangle", t: i * 0.09, dur: 0.38, vol: 0.38 }));
      tone({ f: 98, dur: 1.0, vol: 0.3 });
      noise({ t: 0.5, dur: 0.8, vol: 0.13, from: 4000, to: 9000 });
    },
    dupe() { [880, 660, 880].forEach((f, i) => tone({ f, type: "square", t: i * 0.08, dur: 0.07, vol: 0.15 })); },
    upgrade() {
      tone({ f: 400, f2: 1300, dur: 0.35, vol: 0.32 });
      [784, 988, 1319].forEach((f, i) => tone({ f, type: "triangle", t: 0.26 + i * 0.08, dur: 0.26, vol: 0.38 }));
      noise({ t: 0.4, dur: 0.35, vol: 0.1, from: 4000, to: 8000 });
    },
  };

  return {
    play(name) {
      if (!enabled || !sounds[name]) return;
      try { sounds[name](); } catch { /* audio bị chặn thì bỏ qua */ }
    },
    reveal(rarity, duplicate) {
      if (duplicate) return this.play("dupe");
      if (rarity === "SSS" || rarity === "SS") return this.play("revealEpic");
      if (rarity === "S" || rarity === "A") return this.play("revealRare");
      return this.play("revealCommon");
    },
    get enabled() { return enabled; },
    toggle() {
      enabled = !enabled;
      localStorage.setItem("epux-sfx", enabled ? "on" : "off");
      if (enabled) this.play("claim");
      return enabled;
    },
  };
})();

/* TTS — đọc từ vựng bằng Web Speech API (giọng en-US có sẵn của Windows/Edge).
   Ưu tiên giọng "Natural" của Edge nếu có, không thì Zira/David của Windows. */
const TTS = (() => {
  const ss = window.speechSynthesis;
  let voice = null;

  function pick() {
    if (!ss) return null;
    const en = ss.getVoices().filter((v) => v.lang && v.lang.toLowerCase().startsWith("en"));
    voice =
      en.find((v) => /natural/i.test(v.name) && v.lang === "en-US") ||
      en.find((v) => v.lang === "en-US") ||
      en[0] || null;
    return voice;
  }

  if (ss) {
    pick();
    if (typeof ss.addEventListener === "function") ss.addEventListener("voiceschanged", pick);
  }

  return {
    speak(text, rate = 0.92) {
      if (!ss || !text) return false;
      if (!voice) pick();
      ss.cancel(); // ngắt câu đang đọc dở
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "en-US";
      if (voice) u.voice = voice;
      u.rate = rate;
      u.pitch = 1;
      ss.speak(u);
      return true;
    },
    stop() { ss?.cancel(); },
  };
})();
