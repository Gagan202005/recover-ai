import { useRef, useCallback } from 'react';

const SOUND_URLS = {
  kaching: '/sounds/kaching.mp3',
  blocked: '/sounds/blocked.mp3',
  alert: '/sounds/alert.mp3',
  success: '/sounds/success.mp3',
};

export function useSounds() {
  const audioRefs = useRef({});

  const play = useCallback((soundName) => {
    try {
      if (!audioRefs.current[soundName]) {
        audioRefs.current[soundName] = new Audio(SOUND_URLS[soundName]);
      }
      audioRefs.current[soundName].currentTime = 0;
      audioRefs.current[soundName].play().catch(() => {});
    } catch (e) {
      // Ignore audio errors silently
    }
  }, []);

  return { play };
}
