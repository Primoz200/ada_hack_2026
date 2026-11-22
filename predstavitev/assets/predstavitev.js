// Upravljanje: puščice, preslednica, PageUp/PageDown (daljinec), Home/End, F za cel zaslon, poteg.
// Video se začne ob prihodu na diapozitiv; klik ali V ga ustavi, nadaljuje ali po koncu ponovi.
(() => {
  const root = document.documentElement
  const slides = [...document.querySelectorAll('.slide')]
  const chrome = document.querySelector('.chrome')
  const links = [...chrome.querySelectorAll('nav a')]
  const count = chrome.querySelector('.count')
  const deck = matchMedia('(min-aspect-ratio: 1/1)')
  const still = matchMedia('(prefers-reduced-motion: reduce)')
  const films = slides.map((s) => s.querySelector('video'))
  let playing = null
  let current = 0

  const fromHash = () => {
    const n = Number.parseInt(location.hash.slice(1), 10)
    return Number.isFinite(n) ? n - 1 : 0
  }

  const automatic = () => deck.matches && !still.matches

  function play(video) {
    // če brskalnik zavrne samodejni zagon, ostanejo kontrole
    video.play().catch((e) => { if (e.name !== 'AbortError') video.controls = true })
  }

  function toggle(video) {
    if (video.paused || video.ended) play(video)
    else video.pause()
  }

  // Samo ob menjavi diapozitiva: sprememba velikosti okna videa ne začne znova.
  function syncFilms() {
    const auto = automatic()
    films.forEach((v, i) => {
      if (!v) return
      v.controls = !auto
      if (auto && Math.abs(i - current) <= 1) v.preload = 'auto'
    })
    const next = auto ? films[current] : null
    if (next === playing) return
    playing?.pause()
    playing = next
    if (!next) return
    if (next.readyState) next.currentTime = 0
    play(next)
  }

  function show(index) {
    current = Math.max(0, Math.min(slides.length - 1, index))
    const slide = slides[current]
    slides.forEach((s, i) => {
      s.classList.toggle('active', i === current)
      s.inert = deck.matches && i !== current
    })
    document.body.style.background = deck.matches ? getComputedStyle(slide).backgroundColor : ''
    chrome.classList.toggle('light', slide.matches('.deep, .green, .slate'))
    links.forEach((a) => {
      if (a.dataset.part === slide.dataset.part) a.setAttribute('aria-current', 'step')
      else a.removeAttribute('aria-current')
    })
    count.textContent = `${current + 1} / ${slides.length}`
    syncFilms()
  }

  function go(index) {
    show(index)
    history.replaceState(null, '', `#${current + 1}`)
  }

  function fit() {
    root.style.setProperty('--s', Math.min(innerWidth / 1920, innerHeight / 1080))
    show(current)
  }

  const keys = {
    ArrowRight: () => current + 1, ArrowDown: () => current + 1, PageDown: () => current + 1, ' ': () => current + 1,
    ArrowLeft: () => current - 1, ArrowUp: () => current - 1, PageUp: () => current - 1, Backspace: () => current - 1,
    Home: () => 0, End: () => slides.length - 1,
  }

  addEventListener('keydown', (e) => {
    if (!deck.matches || e.metaKey || e.ctrlKey || e.altKey) return
    if (e.key.toLowerCase() === 'f') {
      if (document.fullscreenElement) document.exitFullscreen()
      else root.requestFullscreen?.()
      return
    }
    if (e.key.toLowerCase() === 'v' && films[current]) {
      toggle(films[current])
      return
    }
    const next = e.key === ' ' && e.shiftKey ? () => current - 1 : keys[e.key]
    if (!next) return
    e.preventDefault()
    go(next())
  })

  let start = null
  addEventListener('touchstart', (e) => {
    start = e.touches.length === 1 ? e.touches[0] : null
  }, { passive: true })
  addEventListener('touchend', (e) => {
    if (!deck.matches || !start) return
    const dx = e.changedTouches[0].clientX - start.clientX
    const dy = e.changedTouches[0].clientY - start.clientY
    start = null
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) go(current + (dx < 0 ? 1 : -1))
  }, { passive: true })

  films.forEach((v) => v?.addEventListener('click', () => {
    if (!v.controls) toggle(v)
  }))
  still.addEventListener('change', syncFilms)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) playing?.pause()
  })
  addEventListener('hashchange', () => show(fromHash()))
  addEventListener('resize', fit)

  current = fromHash()
  fit()
})()
