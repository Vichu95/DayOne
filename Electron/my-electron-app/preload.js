// preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  openFolder: () => ipcRenderer.send('open-folder'),
  openLink: () => ipcRenderer.send('open-link'),
  quitApp: () => ipcRenderer.send('quit-app')
});
