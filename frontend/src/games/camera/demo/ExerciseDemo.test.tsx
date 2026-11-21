import { act, StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Prompt } from '../cues'
import { ExerciseDemo } from './ExerciseDemo'

;(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true

function mount(node: React.ReactNode) {
  const el = document.createElement('div')
  document.body.append(el)
  const root = createRoot(el)
  act(() => root.render(<StrictMode>{node}</StrictMode>))
  return {
    el,
    rerender: (n: React.ReactNode) => act(() => root.render(<StrictMode>{n}</StrictMode>)),
    unmount: () => {
      act(() => root.unmount())
      el.remove()
    },
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('ExerciseDemo', () => {
  it('a fixed phase draws one labelled picture and reports the matching cue word', () => {
    const cues: (Prompt | null)[] = []
    const m = mount(<ExerciseDemo exerciseKey="hand_open_close" hand="right" phase={0.1} onCue={(c) => cues.push(c)} />)
    const img = m.el.querySelector('[role="img"]')
    expect(img?.getAttribute('aria-label')).toMatch(/pest/)
    expect(cues.at(-1)).toBe('open')
    m.rerender(<ExerciseDemo exerciseKey="hand_open_close" hand="right" phase={0.6} onCue={(c) => cues.push(c)} />)
    expect(cues.at(-1)).toBe('close')
    m.unmount()
  })

  it('draws nothing for an exercise it does not know', () => {
    const m = mount(<ExerciseDemo exerciseKey="unknown" detector="pose" hand="right" phase={0} />)
    expect(m.el.innerHTML).toBe('')
    m.unmount()
  })

  it('stops its animation frame loop when unmounted (StrictMode double mount included)', () => {
    let next = 1
    const live = new Set<number>()
    vi.stubGlobal('requestAnimationFrame', () => {
      const id = next++
      live.add(id)
      return id
    })
    vi.stubGlobal('cancelAnimationFrame', (id: number) => live.delete(id))
    const m = mount(<ExerciseDemo exerciseKey="arm_raise" hand="left" />)
    expect(live.size).toBe(1)
    m.unmount()
    expect(live.size).toBe(0)
  })

  it('with reduced motion shows both end positions with both words and no loop', () => {
    vi.stubGlobal('matchMedia', (q: string) => ({
      matches: q.includes('reduce'),
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    }))
    const raf = vi.fn(() => 1)
    vi.stubGlobal('requestAnimationFrame', raf)
    const cues: (Prompt | null)[] = []
    const m = mount(<ExerciseDemo exerciseKey="shoulder_abduction" hand="right" onCue={(c) => cues.push(c)} />)
    expect(m.el.querySelectorAll('svg')).toHaveLength(2)
    expect(m.el.textContent).toContain('Dol')
    expect(m.el.textContent).toContain('Gor')
    expect(raf).not.toHaveBeenCalled()
    expect(cues.at(-1)).toBeNull()
    m.unmount()
  })
})
