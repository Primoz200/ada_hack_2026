import type { ComponentProps } from 'react'
import { cn } from '@/lib/utils'

/** The white, generously rounded surface every screen is built from (DESIGN.md: Panels). */
export function Panel({ className, ...props }: ComponentProps<'section'>) {
  return <section className={cn('rounded-panel bg-card p-8 shadow-panel md:p-10', className)} {...props} />
}

/** Page heading that sits directly on the page background, above the panels. */
export function PageTitle({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4 px-2">
      <h1 className="text-[2.25rem] leading-tight font-bold">{title}</h1>
      {children}
    </div>
  )
}
