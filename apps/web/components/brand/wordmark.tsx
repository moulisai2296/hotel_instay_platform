import { cn } from "@/lib/utils";

/**
 * InStayOS wordmark. On dark (guest) surfaces "Stay" is gold + "OS" cream;
 * on light surfaces it reads navy with a gold "Stay". Size via `className`.
 */
export function Wordmark({
  className,
  tone = "dark",
}: {
  className?: string;
  tone?: "dark" | "light";
}) {
  return (
    <span
      className={cn(
        "font-display font-bold tracking-tight",
        tone === "dark" ? "text-cream" : "text-navy",
        className,
      )}
    >
      <span className="text-gold">Stay</span>
      OS
    </span>
  );
}
