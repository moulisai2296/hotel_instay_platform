"use client";

import Link from "next/link";
import { Compass, MessageCircle } from "lucide-react";

/**
 * Hotel guide. There's no amenities backend yet (no table/endpoint), so this is
 * an honest placeholder that points guests to the concierge for anything they
 * need. Becomes a real amenities directory once the backend lands.
 */
export default function GuidePage({ params }: { params: { slug: string } }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <header className="px-5 pb-2 pt-5">
        <h1 className="font-display text-xl font-bold text-cream">Hotel guide</h1>
        <p className="text-xs text-muted-foreground">Amenities &amp; information</p>
      </header>

      <div className="flex min-h-0 flex-1 flex-col items-center justify-center px-8 text-center">
        <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gold/15">
          <Compass className="h-8 w-8 text-gold" />
        </div>
        <p className="text-sm font-semibold text-cream">Guide coming soon</p>
        <p className="mt-1.5 max-w-[18rem] text-xs text-muted-foreground">
          Your hotel is putting the finishing touches on its amenities directory.
          In the meantime, the concierge can answer anything — pool hours, spa
          bookings, restaurant timings, and more.
        </p>
        <Link
          href={`/h/${params.slug}/chat`}
          className="mt-5 inline-flex items-center gap-2 rounded-full bg-gold px-5 py-2.5 text-sm font-semibold text-navy"
        >
          <MessageCircle className="h-4 w-4" /> Ask the concierge
        </Link>
      </div>
    </div>
  );
}
