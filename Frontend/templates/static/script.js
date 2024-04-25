document.addEventListener('DOMContentLoaded', function() {
  const preferencesOverlay = document.querySelector('.preferences-overlay');
  const preferencesWindow = document.querySelector('.preferences-window');

  // Open preferences window
  function openPreferencesWindow() {
      preferencesOverlay.style.display = 'block';
      preferencesWindow.style.display = 'block';
  }

  // Close preferences window
  function closePreferencesWindow(event) {
      if (event.target === preferencesOverlay) {
          preferencesOverlay.style.display = 'none';
          preferencesWindow.style.display = 'none';
      }
  }

  // Event listener for opening preferences window
  document.getElementById('open-preferences').addEventListener('click', openPreferencesWindow);

  // Event listener for closing preferences window when clicking outside of it
  preferencesOverlay.addEventListener('click', closePreferencesWindow);
});