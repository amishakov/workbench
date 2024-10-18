import { combineReducers } from "redux"

import { timestamp } from "./utils.js"

function activities(state, action) {
  if (typeof state === "undefined") {
    state = {}
  }
  switch (action.type) {
    case "ADD_ACTIVITY":
      return { ...state, [action.activity.id]: action.activity }
    case "REMOVE_ACTIVITY":
      return Object.fromEntries(
        Object.entries(state).filter(([id]) => id !== action.id),
      )
    case "UPDATE_ACTIVITY":
      return {
        ...state,
        [action.id]: {
          ...state[action.id],
          ...action.fields,
        },
      }
    case "START":
    case "STOP": {
      if (!action.current || !state[action.current.id]) return state
      const activity = state[action.current.id]
      return {
        ...state,
        [activity.id]: {
          ...activity,
          seconds: activity.seconds + (timestamp() - action.current.startedAt),
        },
      }
    }
    default:
      return state
  }
}

function current(state, action) {
  if (typeof state === "undefined") {
    state = null
  }
  switch (action.type) {
    case "START":
      return {
        id: action.id,
        startedAt: timestamp(),
      }
    case "STOP":
      return null
    case "REMOVE_ACTIVITY":
      return state && state.id === action.id ? null : state
    default:
      return state
  }
}

function modalActivity(state, action) {
  if (typeof state === "undefined") {
    state = null
  }
  switch (action.type) {
    case "MODAL_ACTIVITY":
      return action.id
    case "UPDATE_ACTIVITY":
      return null
    default:
      return state
  }
}

function projects(state, action) {
  if (typeof state === "undefined") {
    state = []
  }
  switch (action.type) {
    case "PROJECTS":
      return action.projects
    default:
      return state
  }
}

const reducer = combineReducers({
  activities,
  current,
  modalActivity,
  projects,
})

export default reducer
