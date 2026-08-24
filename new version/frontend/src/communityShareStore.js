/**
 * Maps local project ids (surgreview-projects) to community project ids.
 *
 * A local project can be shared to the community at most once; this mapping
 * survives reloads so the Home page can render "已分享" badges and route
 * updates/deletes to the right community project.
 */
const SHARE_MAP_KEY = 'surgreview-share-map'

// Legacy key from before the SurgReview rename. Kept so the share map stored
// under the old name is migrated once below and never lost.
const LEGACY_SHARE_MAP_KEY = 'surginsight-share-map'

function migrateLegacyKey() {
  try {
    if (!localStorage.getItem(SHARE_MAP_KEY) && localStorage.getItem(LEGACY_SHARE_MAP_KEY)) {
      localStorage.setItem(SHARE_MAP_KEY, localStorage.getItem(LEGACY_SHARE_MAP_KEY))
    }
  } catch {
    // localStorage unavailable — leave as-is
  }
}

migrateLegacyKey()

export function getShareMap() {
  try {
    return JSON.parse(localStorage.getItem(SHARE_MAP_KEY) || '{}')
  } catch {
    return {}
  }
}

export function getSharedCommunityId(localProjectId) {
  return getShareMap()[localProjectId] || null
}

export function setSharedCommunityId(localProjectId, communityId) {
  const map = getShareMap()
  map[localProjectId] = communityId
  localStorage.setItem(SHARE_MAP_KEY, JSON.stringify(map))
  return map
}

export function removeSharedProject(localProjectId) {
  const map = getShareMap()
  delete map[localProjectId]
  localStorage.setItem(SHARE_MAP_KEY, JSON.stringify(map))
  return map
}
