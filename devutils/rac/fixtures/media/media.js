// A looping track with Media Session metadata, for shots of rac's sidebar
// media card. Autoplay needs a user activation, so any key or press on the
// page starts it; pause.html also pauses itself after a few seconds.
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
let started = false;

function play() {
  if (started) {
    return;
  }
  audio.play().then(() => {
    started = true;
    document.getElementById('state').textContent = 'Playing';
    if (pauseAfterMs) {
      setTimeout(() => {
        audio.pause();
        document.getElementById('state').textContent = 'Paused';
      }, pauseAfterMs);
    }
  }).catch((error) => {
    document.getElementById('state').textContent = 'Blocked: ' + error.name;
  });
}

addEventListener('keydown', play);
addEventListener('pointerdown', play);
play();
