const DB_NAME = 'surgreview-media'
const DB_VERSION = 1
const STORE_NAME = 'videos'

// Legacy IndexedDB database name from before the SurgReview rename. Videos
// stored there are copied into the new database once (see migrateLegacyDb).
const LEGACY_DB_NAME = 'surginsight-media'

let migrationPromise = null

function ensureMigrated() {
  if (!migrationPromise) {
    migrationPromise = migrateLegacyDb()
  }
  return migrationPromise
}

function rawOpen() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'projectId' })
      }
    }

    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function openDatabase() {
  await ensureMigrated()
  return rawOpen()
}

async function migrateLegacyDb() {
  if (typeof indexedDB === 'undefined') return

  return new Promise((resolve) => {
    let settled = false
    const finish = () => {
      if (!settled) {
        settled = true
        resolve()
      }
    }

    const request = indexedDB.open(LEGACY_DB_NAME)
    request.onerror = () => finish() // legacy DB does not exist — nothing to migrate
    request.onblocked = () => finish()
    request.onsuccess = () => {
      const legacyDb = request.result
      if (!legacyDb.objectStoreNames.contains(STORE_NAME)) {
        legacyDb.close()
        finish()
        return
      }

      const tx = legacyDb.transaction(STORE_NAME, 'readonly')
      const getAll = tx.objectStore(STORE_NAME).getAll()

      getAll.onerror = () => {
        legacyDb.close()
        finish()
      }
      getAll.onsuccess = () => {
        const records = getAll.result
        legacyDb.close()
        if (!records.length) {
          finish()
          return
        }

        rawOpen()
          .then((db) => {
            return new Promise((copyResolve) => {
              const writeTx = db.transaction(STORE_NAME, 'readwrite')
              const store = writeTx.objectStore(STORE_NAME)
              for (const record of records) {
                store.put(record)
              }
              writeTx.oncomplete = () => {
                db.close()
                indexedDB.deleteDatabase(LEGACY_DB_NAME)
                copyResolve()
              }
              writeTx.onerror = () => {
                db.close()
                copyResolve()
              }
            })
          })
          .then(finish)
      }
    }
  })
}

export async function saveProjectVideo(projectId, file) {
  const db = await openDatabase()

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)

    store.put({
      projectId,
      file,
      updatedAt: new Date().toISOString(),
    })

    tx.oncomplete = () => {
      db.close()
      resolve()
    }
    tx.onerror = () => {
      db.close()
      reject(tx.error)
    }
  })
}

export async function getProjectVideo(projectId) {
  const db = await openDatabase()

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)
    const request = store.get(projectId)

    request.onsuccess = () => {
      db.close()
      resolve(request.result?.file || null)
    }
    request.onerror = () => {
      db.close()
      reject(request.error)
    }
  })
}

export async function deleteProjectVideo(projectId) {
  const db = await openDatabase()

  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)
    store.delete(projectId)

    tx.oncomplete = () => {
      db.close()
      resolve()
    }
    tx.onerror = () => {
      db.close()
      reject(tx.error)
    }
  })
}
