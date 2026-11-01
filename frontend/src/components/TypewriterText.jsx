// Letters land one by one, flashing gold before settling into the heading colour.
// `delay` is in seconds, `step` the gap between letters in milliseconds.
export default function TypewriterText({ text, delay = 0.2, step = 45, className = '' }) {
  return (
    <span className={`typewriter ${className}`} aria-label={text}>
      {[...text].map((ch, i) => (
        <span
          key={i}
          aria-hidden="true"
          className="typewriter-letter"
          style={{ animationDelay: `${delay + (i * step) / 1000}s` }}
        >
          {ch === ' ' ? ' ' : ch}
        </span>
      ))}
      <span
        aria-hidden="true"
        className="typewriter-caret"
        style={{ animationDelay: `${delay + (text.length * step) / 1000}s` }}
      />
    </span>
  )
}
