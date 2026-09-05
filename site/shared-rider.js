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

document.title += " – " + RIDER_NAMES[currentRider]

const riderNav = document.querySelector("nav.rider-nav")
if (riderNav) {
  for (const rider of RIDERS) {
    const a = document.createElement("a")
    a.href = onBadgesPage ? `../${rider}/badges.html` : `../${rider}/`
    a.textContent = RIDER_NAMES[rider]
    if (rider === currentRider) a.classList.add("active")
    riderNav.appendChild(a)
  }
}
