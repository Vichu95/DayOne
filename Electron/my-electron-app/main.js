const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');

let mainWindow;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    fullscreen: true,
    title: '',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js') // Add preload script
    }
  });

  mainWindow.loadFile(path.join(__dirname, 'index.html'));
}

function createStartWindow() {
  const startWindow = new BrowserWindow({
    width: 800,
    height: 600,
    fullscreen: true,
    title: '',
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: true,
      preload: path.join(__dirname, 'preload.js') // Add preload script
    }
  });

  startWindow.loadFile(path.join(__dirname, 'start.html'));
}

app.whenReady().then(createMainWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

ipcMain.on('open-folder', () => {
  shell.openPath('/path/to/your/folder');
});

ipcMain.on('open-link', () => {
  shell.openExternal('https://example.com');
});

ipcMain.on('quit-app', () => {
  app.quit();
});
