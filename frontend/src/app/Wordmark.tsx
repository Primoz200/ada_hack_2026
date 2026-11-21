import { Link } from 'react-router'

/** Product wordmark. Our own mark (a traced path), not the zVEM logo. */
export function Wordmark({ to }: { to: string }) {
  return (
    <Link to={to} className="flex items-center gap-2.5 rounded-md text-[1.35rem] leading-none font-bold tracking-tight">
      <svg viewBox="0 0 40 40" className="size-9 text-brand" aria-hidden>
        <circle cx="20" cy="20" r="17" fill="none" stroke="currentColor" strokeWidth="3" />
        <path
          d="M10 22c3 0 3.5-7 6.5-7s3 10 6 10 3-6 7.5-6"
          fill="none"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>
        Okrevanje <span className="text-brand-ink">doma</span>
      </span>
    </Link>
  )
}
