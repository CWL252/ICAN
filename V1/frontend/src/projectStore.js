const PROJECTS_KEY = 'surginsight-projects'
const ACTIVE_PROJECT_KEY = 'surginsight-active-project'

export function getProjects() {
  try {
    return JSON.parse(localStorage.getItem(PROJECTS_KEY) || '[]')
  } catch {
    return []
  }
}

export function saveProject(project) {
  const projects = getProjects()
  const nextProjects = [project, ...projects.filter((item) => item.id !== project.id)]
  localStorage.setItem(PROJECTS_KEY, JSON.stringify(nextProjects))
  return nextProjects
}

export function replaceProjects(projects) {
  localStorage.setItem(PROJECTS_KEY, JSON.stringify(projects))
  return projects
}

export function deleteProject(projectId) {
  const projects = getProjects()
  const nextProjects = projects.filter((item) => item.id !== projectId)
  localStorage.setItem(PROJECTS_KEY, JSON.stringify(nextProjects))

  const activeProject = getActiveProject()
  if (activeProject?.id === projectId) {
    sessionStorage.removeItem(ACTIVE_PROJECT_KEY)
  }

  return nextProjects
}

export function setActiveProject(project) {
  sessionStorage.setItem(ACTIVE_PROJECT_KEY, JSON.stringify(project))
}

export function getActiveProject() {
  try {
    return JSON.parse(sessionStorage.getItem(ACTIVE_PROJECT_KEY) || 'null')
  } catch {
    return null
  }
}
