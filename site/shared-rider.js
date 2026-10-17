// Shared rider detection for the per-rider pages. The rider is derived from
// the first path segment (/martin/, /nils/, /magnus/), so the per-rider HTML
// files are identical copies rendered from a single template.
const RIDERS = ["martin", "nils", "magnus"]
const RIDER_NAMES = { martin: "Martin", nils: "Nils", magnus: "Magnus" }

const currentRider = (() => {
  const seg = location.pathname.split("/").filter(Boolean)[0]
  return RIDERS.includes(seg) ? seg : "martin"
})()

const onBadgesPage = location.pathname.endsWith("badges.html")
const onHistoryPage = location.pathname.endsWith("history.html")

document.title += " – " + RIDER_NAMES[currentRider]

const riderNav = document.querySelector("nav.rider-nav")
if (riderNav) {
  for (const rider of RIDERS) {
    const a = document.createElement("a")
    // Base target; the query string is (re-)applied by syncRiderLinks() so
    // filter/sort settings (?needed=1&date=today, ...) survive rider switches.
    if (onBadgesPage) {
      a.dataset.base = `../${rider}/badges.html`
    } else if (onHistoryPage) {
      a.dataset.base = `../${rider}/history.html`
    } else {
      a.dataset.base = `../${rider}/`
    }
    a.textContent = RIDER_NAMES[rider]
    if (rider === currentRider) a.classList.add("active")
    riderNav.appendChild(a)
  }
}

function syncRiderLinks() {
  const query = location.search + location.hash
  document.querySelectorAll("nav.rider-nav a").forEach((a) => {
    if (a.dataset.base) a.href = a.dataset.base + query
  })
}

syncRiderLinks()

// Filter changes update the URL via history.replaceState after load, so keep
// the rider links in sync with the current query string at all times.
const origReplaceState = history.replaceState.bind(history)
history.replaceState = (...args) => {
  origReplaceState(...args)
  syncRiderLinks()
}
window.addEventListener("popstate", syncRiderLinks)
