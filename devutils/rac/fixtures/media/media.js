// A looping track with Media Session metadata, for shots of rac's sidebar
// media card. Autoplay needs a user activation, so any key or press on the
// page starts it, or starts it again once paused; pause.html also pauses
// itself after a few seconds, once per page load.
const audio = document.getElementById('track');
navigator.mediaSession.metadata = new MediaMetadata({
  title: 'Evening Tide',
  artist: 'The Fixtures',
  album: 'rac',
  artwork: [{src: 'art.png', sizes: '256x256', type: 'image/png'}],
});
navigator.mediaSession.setActionHandler('previoustrack', () => {
  audio.currentTime = 0;
});
navigator.mediaSession.setActionHandler('nexttrack', () => {
  audio.currentTime = 0;
});

const pauseAfterMs = Number(document.body.dataset.pauseAfterMs || 0);
const state = document.getElementById('state');
let autoPauseScheduled = false;

// The label follows the audio itself, so playing or pausing from rac's
// sidebar card shows here too.
audio.addEventListener('play', () => {
  state.textContent = 'Playing';
});
audio.addEventListener('pause', () => {
  state.textContent = 'Paused';
});

function play() {
  if (!audio.paused) {
    return;
  }
  audio.play().then(() => {
    // pause.html pauses itself once per page load.
    if (pauseAfterMs && !autoPauseScheduled) {
      autoPauseScheduled = true;
      setTimeout(() => audio.pause(), pauseAfterMs);
    }
  }).catch((error) => {
    state.textContent = 'Blocked: ' + error.name;
  });
}

addEventListener('keydown', play);
addEventListener('pointerdown', play);
play();
