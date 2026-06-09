/**
 * Guest route-group shell. Forces the dark (navy/gold) theme and constrains to
 * a mobile-first column — the guest surface is the guest's own phone
 * (docs/API.md §4, GUEST_ACCESS_MODE=mobile).
 */
export default function GuestLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="dark min-h-dvh bg-background text-foreground">
      <div className="mx-auto flex min-h-dvh w-full max-w-md flex-col">
        {children}
      </div>
    </div>
  );
}
