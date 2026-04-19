// =====================================================================
// BeatMind.xo — app.js
// =====================================================================

// ---- DOM refs ----
const uploadZone     = document.getElementById('uploadZone');
const fileInput      = document.getElementById('fileInput');
const uploadSection  = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const gameSection    = document.getElementById('gameSection');
const resultsSection = document.getElementById('resultsSection');
const uploadPrompt   = document.getElementById('uploadPrompt');

const genreGrid      = document.getElementById('genreGrid');
const skipGameBtn    = document.getElementById('skipGameBtn');

const trackInfoCard  = document.getElementById('trackInfoCard');
const trackArtEl     = document.getElementById('trackArt');
const trackTitleEl   = document.getElementById('trackTitle');
const trackArtistEl  = document.getElementById('trackArtist');
const trackAlbumEl   = document.getElementById('trackAlbum');
const trackVideoLink = document.getElementById('trackVideoLink');

const playPauseBtn   = document.getElementById('playPauseBtn');
const playIcon       = document.getElementById('playIcon');
const pauseIcon      = document.getElementById('pauseIcon');
const vinylRecord    = document.getElementById('vinylRecord');

const primaryGenreEl = document.getElementById('primaryGenre');
const genreBadgeEl   = document.getElementById('genreBadge');
const genreFact      = document.getElementById('genreFact');
const bpmVal         = document.getElementById('bpmVal');
const confidenceVal  = document.getElementById('confidenceVal');
const genreEmoji     = document.getElementById('genreEmoji');
const genreStatVal   = document.getElementById('genreStatVal');

const confidenceBarsEl = document.getElementById('confidenceBars');
const barsToggleBtn    = document.getElementById('barsToggle');
const shareBtn         = document.getElementById('shareBtn');
const resetBtn         = document.getElementById('resetBtn');

const historySidebar   = document.getElementById('historySidebar');
const historyList      = document.getElementById('historyList');
const emptyHistory     = document.getElementById('emptyHistory');
const sidebarToggle    = document.getElementById('sidebarToggle');
const scoreBoard       = document.getElementById('scoreBoard');
const scoreValueEl     = document.getElementById('scoreValue');

const vizCanvas = document.getElementById('vizCanvas');
const vizCtx    = vizCanvas ? vizCanvas.getContext('2d') : null;

// ---- State ----
let wavesurfer      = null;
let currentAudioUrl = null;
let pendingData     = null;        // Holds API response while game-mode is active
let currentData     = null;
let showingAllBars  = false;
let sessionHistory  = [];
let score = { correct: 0, total: 0 };
let audioCtx        = null;
let analyserNode    = null;
let vizRafId        = null;

// ---- Genre meta ----
const genreMeta = {
    rock:       { a1:'#ff4757', a2:'#ffa502', glow:'rgba(255,71,87,0.4)',    emoji:'🎸', mood:'High-energy & raw' },
    jazz:       { a1:'#3742fa', a2:'#70a1ff', glow:'rgba(55,66,250,0.4)',    emoji:'🎷', mood:'Smooth & soulful' },
    electronic: { a1:'#2ed573', a2:'#1e90ff', glow:'rgba(46,213,115,0.4)',   emoji:'🎛️', mood:'Futuristic & pulsing' },
    classical:  { a1:'#eccc68', a2:'#ff7f50', glow:'rgba(236,204,104,0.4)', emoji:'🎹', mood:'Timeless & grand' },
    blues:      { a1:'#a29bfe', a2:'#6c5ce7', glow:'rgba(108,92,231,0.4)',   emoji:'🎺', mood:'Deep & heartfelt' },
    country:    { a1:'#fdcb6e', a2:'#e17055', glow:'rgba(253,203,110,0.4)', emoji:'🤠', mood:'Warm & twangy' },
    hiphop:     { a1:'#fd79a8', a2:'#e84393', glow:'rgba(253,121,168,0.4)', emoji:'🎤', mood:'Rhythmic & bold' },
    metal:      { a1:'#b2bec3', a2:'#636e72', glow:'rgba(99,110,114,0.4)',   emoji:'🤘', mood:'Intense & heavy' },
    pop:        { a1:'#fd79a8', a2:'#fdcb6e', glow:'rgba(253,121,168,0.4)', emoji:'🎵', mood:'Catchy & uplifting' },
    reggae:     { a1:'#00b894', a2:'#fdcb6e', glow:'rgba(0,184,148,0.4)',    emoji:'🌴', mood:'Laid-back & groovy' },
    default:    { a1:'#6c5ce7', a2:'#00cec9', glow:'rgba(108,92,231,0.4)',   emoji:'🎵', mood:'Musical & vibrant' },
};

const genreFacts = {
    rock:       ["Rock music grew from rock 'n' roll in the late 1950s.", "The electric guitar is rock's defining instrument.", "Led Zeppelin sold over 300 million records worldwide."],
    jazz:       ["Jazz originated in New Orleans in the early 20th century.", "Jazz musicians often improvise in real time.", "Miles Davis's 'Kind of Blue' is the best-selling jazz album ever."],
    classical:  ["Beethoven composed his greatest works while deaf.", "Mozart wrote his first symphony at age 8.", "A full orchestra can have over 100 musicians."],
    electronic: ["Electronic music exploded in the 1960s with synthesizers.", "Daft Punk won 5 Grammy Awards for 'Random Access Memories'.", "The TR-808 drum machine shaped hip-hop and electronic music."],
    blues:      ["Blues originated in the Deep South around the 1870s.", "The 12-bar blues progression is the backbone of countless songs.", "B.B. King's guitar was named 'Lucille' after a woman in a bar fight."],
    country:    ["Country music originated in the Southern United States in the 1920s.", "Nashville, Tennessee is the world capital of country music.", "Johnny Cash performed at Folsom Prison in 1968."],
    hiphop:     ["Hip-hop was born in the Bronx, New York in the 1970s.", "The Sugarhill Gang's 'Rapper's Delight' was the first rap Top 40 hit.", "Eminem holds the Guinness record for fastest rap — 11.08 syllables/sec."],
    metal:      ["Black Sabbath is credited as the first heavy metal band.", "Metallica's 'Black Album' sold over 30 million copies.", "The word 'metal' in music comes from a Steppenwolf song lyric."],
    pop:        ["'Pop' is short for 'popular music'.", "Michael Jackson's 'Thriller' is the best-selling album of all time.", "Pop music typically features short, catchy, hook-driven structures."],
    reggae:     ["Reggae originated in Jamaica in the late 1960s.", "Bob Marley is the most famous reggae musician ever.", "The word 'reggae' comes from Jamaican patois meaning 'rags'."],
};

function getRandomFact(genre) {
    const facts = genreFacts[genre.toLowerCase()] || [];
    if (!facts.length) return '';
    return facts[Math.floor(Math.random() * facts.length)];
}

function getMeta(genre) {
    return genreMeta[genre.toLowerCase()] || genreMeta.default;
}

// =====================================================================
// WAVESURFER + VISUALIZER
// =====================================================================
function setupPlayer(file) {
    if (wavesurfer) wavesurfer.destroy();
    if (currentAudioUrl) URL.revokeObjectURL(currentAudioUrl);
    if (vizRafId) { cancelAnimationFrame(vizRafId); vizRafId = null; }
    analyserNode = null;

    currentAudioUrl = URL.createObjectURL(file);

    wavesurfer = WaveSurfer.create({
        container:     '#waveform',
        waveColor:     'rgba(255,255,255,0.2)',
        progressColor: genreMeta.default.a1,
        barWidth:      3,
        barRadius:     3,
        cursorWidth:   0,
        height:        40,
    });

    wavesurfer.load(currentAudioUrl);

    wavesurfer.on('ready', () => {
        setupVisualizer();
    });

    wavesurfer.on('finish', () => {
        playIcon.style.display  = 'block';
        pauseIcon.style.display = 'none';
        vinylRecord.classList.remove('spinning');
    });
}

function setupVisualizer() {
    try {
        const mediaEl = wavesurfer.getMediaElement();
        if (!mediaEl) return;
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        if (!mediaEl._bmxConnected) {
            const source = audioCtx.createMediaElementSource(mediaEl);
            analyserNode = audioCtx.createAnalyser();
            analyserNode.fftSize = 64;
            source.connect(analyserNode);
            analyserNode.connect(audioCtx.destination);
            mediaEl._bmxConnected = true;
        }
        drawViz();
    } catch (e) {
        console.warn('Visualizer not available:', e);
    }
}

function drawViz() {
    if (vizRafId) cancelAnimationFrame(vizRafId);
    if (!analyserNode || !vizCanvas || !vizCtx) return;

    const bufLen  = analyserNode.frequencyBinCount;
    const dataArr = new Uint8Array(bufLen);

    const tick = () => {
        vizRafId = requestAnimationFrame(tick);
        const W = vizCanvas.offsetWidth;
        const H = vizCanvas.offsetHeight;
        if (W === 0) return;
        vizCanvas.width  = W * devicePixelRatio;
        vizCanvas.height = H * devicePixelRatio;
        vizCtx.scale(devicePixelRatio, devicePixelRatio);

        analyserNode.getByteFrequencyData(dataArr);
        vizCtx.clearRect(0, 0, W, H);

        const cStyle = getComputedStyle(document.documentElement);
        const color  = (cStyle.getPropertyValue('--a1') || '#6c5ce7').trim();
        const color2 = (cStyle.getPropertyValue('--a2') || '#00cec9').trim();

        const barW = (W / bufLen) * 2.2;
        let x = 0;
        for (let i = 0; i < bufLen; i++) {
            const barH = (dataArr[i] / 255) * H;
            if (barH < 1) { x += barW + 2; continue; }
            const grad = vizCtx.createLinearGradient(0, H, 0, H - barH);
            grad.addColorStop(0, color  + '55');
            grad.addColorStop(1, color2 + 'cc');
            vizCtx.fillStyle = grad;
            vizCtx.beginPath();
            if (vizCtx.roundRect) {
                vizCtx.roundRect(x, H - barH, barW - 1, barH, 2);
            } else {
                vizCtx.rect(x, H - barH, barW - 1, barH);
            }
            vizCtx.fill();
            x += barW + 2;
        }
    };
    tick();
}

// ---- Play / Pause ----
playPauseBtn.addEventListener('click', () => {
    if (!wavesurfer) return;
    if (audioCtx && audioCtx.state === 'suspended') audioCtx.resume();
    wavesurfer.playPause();
    const playing = wavesurfer.isPlaying();
    playIcon.style.display  = playing ? 'none'  : 'block';
    pauseIcon.style.display = playing ? 'block' : 'none';
    playing ? vinylRecord.classList.add('spinning') : vinylRecord.classList.remove('spinning');
});

// =====================================================================
// DRAG & DROP / FILE SELECTION
// =====================================================================
uploadZone.addEventListener('click', () => fileInput.click());

['dragenter','dragover','dragleave','drop'].forEach(e =>
    uploadZone.addEventListener(e, ev => { ev.preventDefault(); ev.stopPropagation(); })
);
['dragenter','dragover'].forEach(e => uploadZone.addEventListener(e, () => uploadZone.classList.add('dragover')));
['dragleave','drop'].forEach(e    => uploadZone.addEventListener(e, () => uploadZone.classList.remove('dragover')));
uploadZone.addEventListener('drop',   e => handleFiles(e.dataTransfer.files));
fileInput.addEventListener('change',  e => { if (e.target.files.length) handleFiles(e.target.files); });

const VALID_EXT = ['.wav','.mp3','.ogg','.flac','.m4a','.wma','.aac','.mp4','.mov','.avi'];

function handleFiles(files) {
    const file = files[0];
    const valid = file.type.includes('audio') || file.type.includes('video') ||
                  VALID_EXT.some(ext => file.name.toLowerCase().endsWith(ext));
    if (!valid) {
        uploadPrompt.innerHTML = '<span class="error-message">Please upload an audio or video file.</span>';
        return;
    }
    setupPlayer(file);
    uploadFile(file);
}

// =====================================================================
// API CALL
// =====================================================================
let lastFile = null;

async function uploadFile(file) {
    lastFile = file;
    show(loadingSection);
    hide(uploadSection);

    const form = new FormData();
    form.append('audio_file', file);

    try {
        const res  = await fetch('/api/predict', { method:'POST', body:form });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Failed to process audio');
        pendingData = data;
        showGameMode(data);
    } catch (err) {
        hide(loadingSection);
        show(uploadSection);
        uploadPrompt.innerHTML = `<span class="error-message">${err.message}</span>`;
    }
}

// =====================================================================
// GAME MODE
// =====================================================================
function showGameMode(data) {
    hide(loadingSection);
    show(gameSection);

    genreGrid.innerHTML = '';
    const options = data.genre_options || [];
    options.forEach(genre => {
        const gk   = genre.toLowerCase();
        const meta = getMeta(gk);
        const card = document.createElement('div');
        card.className = 'genre-card';
        card.dataset.genre = gk;
        card.innerHTML = `<span class="card-emoji">${meta.emoji}</span><span>${genre}</span>`;
        card.addEventListener('click', () => handleGuess(genre, data));
        genreGrid.appendChild(card);
    });
}

function handleGuess(guessedGenre, data) {
    const correct = guessedGenre.toLowerCase() === data.predicted_genre.toLowerCase();
    score.total++;
    if (correct) score.correct++;
    updateScore();

    // Mark all cards
    document.querySelectorAll('.genre-card').forEach(card => {
        const cg = card.dataset.genre;
        if (cg === data.predicted_genre.toLowerCase()) {
            card.classList.add('reveal', 'correct');
        } else if (cg === guessedGenre.toLowerCase() && !correct) {
            card.classList.add('reveal', 'wrong');
        } else {
            card.classList.add('reveal');
        }
    });

    if (correct) {
        launchConfetti();
        setTimeout(() => showFullResults(data), 1200);
    } else {
        setTimeout(() => showFullResults(data), 1500);
    }
}

skipGameBtn.addEventListener('click', () => {
    if (pendingData) showFullResults(pendingData);
});

// =====================================================================
// FULL RESULTS
// =====================================================================
function showFullResults(data) {
    hide(gameSection);
    show(resultsSection);
    currentData     = data;
    showingAllBars  = false;

    const genreKey = data.predicted_genre.toLowerCase();
    const meta     = getMeta(genreKey);

    // Title + badge + fact
    primaryGenreEl.textContent = data.predicted_genre;
    genreBadgeEl.innerHTML     = `<span>${meta.emoji}</span><span>${meta.mood}</span>`;
    genreFact.textContent      = getRandomFact(genreKey);

    // Stats bar
    bpmVal.textContent       = data.bpm ? `${data.bpm} BPM` : '— BPM';
    const topProb            = data.probabilities?.[0]?.probability ?? 0;
    confidenceVal.textContent = topProb ? `${(topProb * 100).toFixed(0)}% confident` : '—';
    genreEmoji.textContent   = meta.emoji;
    genreStatVal.textContent = data.predicted_genre;

    // Dynamic theming
    applyTheme(meta);
    if (wavesurfer) wavesurfer.setOptions({ progressColor: meta.a1 });

    // Track info
    renderTrackInfo(data.track_meta, data.predicted_genre, lastFile?.name);

    // Confidence bars (top 3 by default)
    if (!data.probabilities?.length) data.probabilities = [{ genre: data.predicted_genre, probability: 1.0 }];
    renderBars(data.probabilities.slice(0, 3));
    if (data.probabilities.length > 3) {
        barsToggleBtn.style.display = 'inline-block';
        barsToggleBtn.textContent   = `Show all ${data.probabilities.length} genres ▾`;
    } else {
        barsToggleBtn.style.display = 'none';
    }

    // History
    addToHistory({ name: lastFile?.name || 'Unknown', data, url: currentAudioUrl });
}

// ---- bars toggle ----
barsToggleBtn.addEventListener('click', () => {
    showingAllBars = !showingAllBars;
    if (!currentData) return;
    renderBars(showingAllBars ? currentData.probabilities : currentData.probabilities.slice(0, 3));
    barsToggleBtn.textContent = showingAllBars
        ? 'Show top 3 ▴'
        : `Show all ${currentData.probabilities.length} genres ▾`;
});

function renderBars(probs) {
    confidenceBarsEl.innerHTML = '';
    probs.forEach((prob, i) => {
        const pct  = (prob.probability * 100).toFixed(1);
        const gk   = prob.genre.toLowerCase();
        const em   = getMeta(gk).emoji;
        const col  = getMeta(gk).a1;
        confidenceBarsEl.insertAdjacentHTML('beforeend', `
            <div class="confidence-item">
                <div class="confidence-header">
                    <span>${em} ${prob.genre}</span><span>${pct}%</span>
                </div>
                <div class="confidence-bar-bg">
                    <div class="confidence-bar-fill" id="bar-${i}" style="background:${col}"></div>
                </div>
            </div>`);
        setTimeout(() => {
            const bar = document.getElementById(`bar-${i}`);
            if (bar) bar.style.width = `${pct}%`;
        }, 80 + i * 130);
    });
}

// ---- Track info card ----
function renderTrackInfo(meta, genre, filename) {
    if (!meta) { trackInfoCard.style.display = 'none'; return; }
    const title  = meta.title  || filename || 'Unknown Track';
    const artist = meta.artist || 'Unknown Artist';
    const album  = meta.album  || '';
    const year   = meta.year   ? ` (${meta.year})` : '';

    trackTitleEl.textContent  = title;
    trackArtistEl.textContent = artist;
    trackAlbumEl.textContent  = album ? `${album}${year}` : '';

    if (meta.album_art) {
        trackArtEl.src = meta.album_art;
    } else {
        trackArtEl.src = 'https://placehold.co/80x80/0b0c10/a0aab2?text=♪';
    }

    const ytQ = encodeURIComponent(
        artist !== 'Unknown Artist' ? `${artist} ${title} official` : `${genre} music official`
    );
    trackVideoLink.href = `https://www.youtube.com/results?search_query=${ytQ}`;
    trackInfoCard.style.display = 'flex';
}

// =====================================================================
// DYNAMIC THEMING
// =====================================================================
function applyTheme(meta) {
    document.documentElement.style.setProperty('--a1',   meta.a1);
    document.documentElement.style.setProperty('--a2',   meta.a2);
    document.documentElement.style.setProperty('--glow', meta.glow);
}

// =====================================================================
// SHARE
// =====================================================================
shareBtn.addEventListener('click', async () => {
    if (!currentData) return;
    const pct  = currentData.probabilities?.[0]
        ? `${(currentData.probabilities[0].probability*100).toFixed(0)}%` : '';
    const text = `🎵 BeatMind.xo classified my track as ${pct} ${currentData.predicted_genre.toUpperCase()}! Try it out.`;
    try {
        await navigator.clipboard.writeText(text);
        shareBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        shareBtn.classList.add('copied');
        setTimeout(() => {
            shareBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg> Share Result`;
            shareBtn.classList.remove('copied');
        }, 2500);
    } catch { shareBtn.textContent = 'Copy failed'; }
});

// =====================================================================
// CONFETTI
// =====================================================================
function launchConfetti() {
    if (typeof confetti === 'undefined') return;
    const meta = getMeta(currentData?.predicted_genre || 'default');
    confetti({ particleCount:120, spread:70, origin:{y:0.6}, colors:[meta.a1, meta.a2, '#ffffff'] });
}

// =====================================================================
// SCORE BOARD
// =====================================================================
function updateScore() {
    scoreBoard.style.display = 'flex';
    scoreValueEl.textContent = `${score.correct} / ${score.total}`;
    scoreValueEl.classList.remove('bump');
    void scoreValueEl.offsetWidth; // force reflow for re-animation
    scoreValueEl.classList.add('bump');
}

// =====================================================================
// SIDEBAR HISTORY
// =====================================================================
sidebarToggle.addEventListener('click', () => historySidebar.classList.toggle('open'));

function addToHistory(entry) {
    sessionHistory.unshift(entry);
    if (emptyHistory) emptyHistory.style.display = 'none';

    const gk   = entry.data.predicted_genre.toLowerCase();
    const em   = getMeta(gk).emoji;
    const li   = document.createElement('li');
    li.className = 'history-item';
    li.innerHTML = `<div class="hi-name">${entry.name}</div><div class="hi-genre">${em} ${entry.data.predicted_genre}</div>`;
    li.addEventListener('click', () => {
        hide(uploadSection); hide(gameSection); hide(loadingSection);
        show(resultsSection);
        showFullResults(entry.data);
        historySidebar.classList.remove('open');
    });
    historyList.insertBefore(li, historyList.firstChild);

    // Briefly show sidebar
    historySidebar.classList.add('open');
    setTimeout(() => historySidebar.classList.remove('open'), 1800);
}

// =====================================================================
// KEYBOARD SHORTCUTS
// =====================================================================
document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT') return;
    switch (e.key.toLowerCase()) {
        case ' ':
            e.preventDefault();
            if (wavesurfer && resultsSection.style.display !== 'none') playPauseBtn.click();
            break;
        case 'r':
            if (resultsSection.style.display !== 'none') resetBtn.click();
            break;
        case 's':
            if (resultsSection.style.display !== 'none') shareBtn.click();
            break;
    }
});

// =====================================================================
// RESET
// =====================================================================
resetBtn.addEventListener('click', () => {
    if (wavesurfer) { wavesurfer.pause(); }
    playIcon.style.display  = 'block';
    pauseIcon.style.display = 'none';
    vinylRecord.classList.remove('spinning');

    hide(resultsSection);
    hide(gameSection);
    hide(loadingSection);
    show(uploadSection);

    fileInput.value = '';
    uploadPrompt.textContent = 'Drag & Drop Audio';
    currentData  = null;
    pendingData  = null;
    lastFile     = null;
});

// =====================================================================
// HELPERS
// =====================================================================
function show(el) { if (el) el.style.display = ''; }
function hide(el) { if (el) el.style.display = 'none'; }
