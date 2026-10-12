(function () {
  const script = document.currentScript;
  if (!script) return;

  const configUrl = script.dataset.configUrl;
  const exportUrl = script.dataset.exportUrl;
  const settingsUrl = script.dataset.settingsUrl;
  const auto = script.dataset.auto === '1';
  const panel = script.dataset.panel === '1';
  const DB_NAME = 'prpc-backup';
  const STORE = 'handles';
  const HANDLE_KEY = 'directory';
  const LAST_KEY = 'prpc-backup-last';
  const LOCK_KEY = 'prpc-backup-lock';
  const FOLDER_KEY = 'prpc-backup-folder';
  const LOCK_MS = 120000;
  let cachedHandle = null;
  let activeLock = null;
  let running = false;

  function openDb() {
    return new Promise(function (resolve, reject) {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = function () {
        if (!request.result.objectStoreNames.contains(STORE)) {
          request.result.createObjectStore(STORE);
        }
      };
      request.onsuccess = function () { resolve(request.result); };
      request.onerror = function () { reject(request.error); };
    });
  }

  function idbGet(db, key) {
    return new Promise(function (resolve, reject) {
      const request = db.transaction(STORE, 'readonly').objectStore(STORE).get(key);
      request.onsuccess = function () { resolve(request.result || null); };
      request.onerror = function () { reject(request.error); };
    });
  }

  function idbSet(db, key, value) {
    return new Promise(function (resolve, reject) {
      const tx = db.transaction(STORE, 'readwrite');
      tx.objectStore(STORE).put(value, key);
      tx.oncomplete = function () { resolve(); };
      tx.onerror = function () { reject(tx.error); };
    });
  }

  function getHandle() {
    return openDb().then(function (db) {
      return idbGet(db, HANDLE_KEY);
    }).catch(function () {
      return null;
    });
  }

  function saveHandle(handle) {
    cachedHandle = handle;
    try {
      localStorage.setItem(FOLDER_KEY, handle.name || '');
    } catch (error) {}
    return openDb().then(function (db) {
      return idbSet(db, HANDLE_KEY, handle);
    });
  }

  function readLock() {
    try {
      return JSON.parse(localStorage.getItem(LOCK_KEY) || 'null');
    } catch (error) {
      return null;
    }
  }

  function acquireLock() {
    const now = Date.now();
    const current = readLock();
    if (current && now - current.at < LOCK_MS) return null;
    const id = Math.random().toString(36).slice(2) + now.toString(36);
    localStorage.setItem(LOCK_KEY, JSON.stringify({ id: id, at: now }));
    const check = readLock();
    if (!check || check.id !== id) return null;
    return id;
  }

  function releaseLock(id) {
    const current = readLock();
    if (current && current.id === id) localStorage.removeItem(LOCK_KEY);
  }

  function showNotice(message, link) {
    let box = document.getElementById('prpc-backup-notice');
    if (!box) {
      box = document.createElement('div');
      box.id = 'prpc-backup-notice';
      box.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:1040;max-width:320px;background:#fff7ed;color:#9a3412;border:1px solid #fdba74;border-radius:10px;padding:10px 12px;font-size:13px;line-height:1.45;box-shadow:0 8px 24px rgba(0,0,0,.12);';
      document.body.appendChild(box);
    }
    box.textContent = '';
    box.appendChild(document.createTextNode(message));
    if (link && settingsUrl) {
      const anchor = document.createElement('a');
      anchor.href = settingsUrl;
      anchor.textContent = '설정';
      anchor.style.marginLeft = '8px';
      anchor.style.fontWeight = '700';
      box.appendChild(anchor);
    }
  }

  function hideNotice() {
    const box = document.getElementById('prpc-backup-notice');
    if (box) box.remove();
  }

  function fetchConfig() {
    return fetch(configUrl, { credentials: 'same-origin', cache: 'no-store' }).then(function (response) {
      const type = response.headers.get('content-type') || '';
      if (!response.ok || type.indexOf('json') === -1) return null;
      return response.json();
    });
  }

  function parseStamp(name) {
    const match = /^예약백업_(\d{8})_(\d{6})\.xlsx$/.exec(name);
    if (!match) return null;
    const day = match[1];
    const time = match[2];
    return new Date(
      Number(day.slice(0, 4)),
      Number(day.slice(4, 6)) - 1,
      Number(day.slice(6, 8)),
      Number(time.slice(0, 2)),
      Number(time.slice(2, 4)),
      Number(time.slice(4, 6))
    ).getTime();
  }

  function prune(handle, retentionDays) {
    const cutoff = Date.now() - retentionDays * 86400000;
    const names = [];
    const walk = handle.entries();
    function next() {
      return walk.next().then(function (step) {
        if (step.done) return names;
        const name = step.value[0];
        const entry = step.value[1];
        if (entry.kind === 'file') {
          const stamp = parseStamp(name);
          if (stamp !== null && stamp < cutoff) names.push(name);
        }
        return next();
      });
    }
    return next().then(function () {
      return names.reduce(function (chain, name) {
        return chain.then(function () { return handle.removeEntry(name); });
      }, Promise.resolve());
    });
  }

  function writeBackup(handle, retentionDays) {
    return fetch(exportUrl, { credentials: 'same-origin', cache: 'no-store' }).then(function (response) {
      const type = response.headers.get('content-type') || '';
      const stamp = response.headers.get('X-Backup-Stamp') || '';
      if (!response.ok || type.indexOf('spreadsheet') === -1 || !/^\d{8}_\d{6}$/.test(stamp)) {
        throw new Error('export failed');
      }
      return response.blob().then(function (blob) {
        const name = '예약백업_' + stamp + '.xlsx';
        return handle.getFileHandle(name, { create: true }).then(function (fileHandle) {
          return fileHandle.createWritable().then(function (writable) {
            return writable.write(blob).then(function () {
              return writable.close();
            });
          });
        }).then(function () {
          localStorage.setItem(LAST_KEY, String(Date.now()));
          return prune(handle, retentionDays).catch(function () {});
        });
      });
    });
  }

  function backup(force) {
    if (running) return Promise.resolve();
    return fetchConfig().then(function (config) {
      if (!config) {
        if (force) showNotice('백업 설정을 불러오지 못했습니다.', true);
        return;
      }
      if (!force && !config.enabled) {
        hideNotice();
        return;
      }
      if (!window.showDirectoryPicker) {
        showNotice('이 브라우저는 폴더 저장을 지원하지 않습니다. Chrome 또는 Edge를 사용해 주세요.', true);
        return;
      }
      return getHandle().then(function (handle) {
        cachedHandle = handle;
        if (!handle) {
          showNotice('백업 폴더가 선택되지 않았습니다.', true);
          return;
        }
        const query = handle.queryPermission
          ? handle.queryPermission({ mode: 'readwrite' })
          : Promise.resolve('granted');
        return query.then(function (perm) {
          if (perm !== 'granted') {
            showNotice('백업 폴더 권한이 필요합니다.', true);
            return;
          }
          if (!force) {
            const last = Number(localStorage.getItem(LAST_KEY) || '0');
            const interval = Math.max(5, Number(config.interval_minutes) || 10) * 60000;
            if (last && Date.now() - last < interval) return;
          }
          const lockId = acquireLock();
          if (!lockId) return;
          activeLock = lockId;
          running = true;
          const days = Math.min(30, Math.max(1, Number(config.retention_days) || 3));
          return writeBackup(handle, days).then(function () {
            hideNotice();
            if (panel) return refreshPanel();
          }).catch(function () {
            showNotice('백업에 실패했습니다. 잠시 후 다시 시도합니다.', true);
          }).then(function () {
            running = false;
            releaseLock(lockId);
            if (activeLock === lockId) activeLock = null;
          });
        });
      });
    }).catch(function () {
      if (force) showNotice('백업에 실패했습니다. 잠시 후 다시 시도합니다.', true);
    });
  }

  function chooseFolder() {
    if (!window.showDirectoryPicker) {
      showNotice('이 브라우저는 폴더 저장을 지원하지 않습니다. Chrome 또는 Edge를 사용해 주세요.', false);
      return;
    }
    window.showDirectoryPicker({ mode: 'readwrite' }).then(function (handle) {
      return saveHandle(handle);
    }).then(refreshPanel).catch(function () {});
  }

  function grantPermission() {
    if (cachedHandle && cachedHandle.requestPermission) {
      cachedHandle.requestPermission({ mode: 'readwrite' }).then(function () {
        return refreshPanel();
      }).catch(function () {});
      return;
    }
    chooseFolder();
  }

  function backupNow() {
    if (!cachedHandle) {
      if (!window.showDirectoryPicker) {
        showNotice('이 브라우저는 폴더 저장을 지원하지 않습니다. Chrome 또는 Edge를 사용해 주세요.', false);
        return;
      }
      window.showDirectoryPicker({ mode: 'readwrite' }).then(function (handle) {
        return saveHandle(handle).then(function () { return backup(true); });
      }).catch(function () {});
      return;
    }
    if (cachedHandle.requestPermission) {
      cachedHandle.requestPermission({ mode: 'readwrite' }).then(function (perm) {
        if (perm === 'granted') backup(true);
        else showNotice('백업 폴더 권한이 필요합니다.', true);
      }).catch(function () {});
      return;
    }
    backup(true);
  }

  function refreshPanel() {
    if (!panel) return Promise.resolve();
    const folder = document.getElementById('backup-folder-name');
    const last = document.getElementById('backup-last');
    const permission = document.getElementById('backup-permission');
    return getHandle().then(function (handle) {
      cachedHandle = handle;
      const storedName = localStorage.getItem(FOLDER_KEY) || '';
      if (folder) folder.textContent = handle ? (handle.name || storedName || '선택됨') : '선택 안 됨';
      if (last) {
        const value = Number(localStorage.getItem(LAST_KEY) || '0');
        last.textContent = value ? new Date(value).toLocaleString('ko-KR') : '없음';
      }
      if (!permission) return;
      if (!window.showDirectoryPicker) {
        permission.textContent = 'Chrome 또는 Edge에서만 폴더에 저장할 수 있습니다.';
      } else if (!handle) {
        permission.textContent = '이 브라우저에서 폴더를 한 번 선택해야 합니다.';
      } else if (handle.queryPermission) {
        return handle.queryPermission({ mode: 'readwrite' }).then(function (state) {
          permission.textContent = state === 'granted'
            ? '이 브라우저에 저장 권한이 있습니다.'
            : '폴더 권한을 다시 허용해야 합니다.';
        });
      } else {
        permission.textContent = '폴더가 선택되어 있습니다.';
      }
    }).catch(function () {
      if (folder) folder.textContent = '선택 안 됨';
    });
  }

  window.PrpcBackup = {
    pickFolder: chooseFolder,
    grantPermission: grantPermission,
    backupNow: backupNow,
  };

  const pickButton = document.getElementById('backup-pick');
  const grantButton = document.getElementById('backup-grant');
  const nowButton = document.getElementById('backup-now');
  if (pickButton) pickButton.addEventListener('click', chooseFolder);
  if (grantButton) grantButton.addEventListener('click', grantPermission);
  if (nowButton) nowButton.addEventListener('click', backupNow);
  if (panel) refreshPanel();
  if (auto) {
    window.setTimeout(function () { backup(false); }, 1500);
    window.setInterval(function () { backup(false); }, 30000);
  }
  window.addEventListener('pagehide', function () {
    if (activeLock) releaseLock(activeLock);
  });
})();
