import { cn } from "@/lib/utils";

interface LightBulbIconProps {
  isOn: boolean;
}

export const LightBulbIcon = ({ isOn }: LightBulbIconProps) => (
  <svg
    viewBox="0 0 64 64"
    role="img"
    aria-hidden="true"
    className={cn("light-bulb-icon", isOn ? "light-bulb-icon--on" : "light-bulb-icon--off")}
  >
    <path
      className="light-bulb-glass"
      d="M32 6C20.954 6 12 14.954 12 26c0 7.01 3.646 13.28 9.59 16.86 1.56.92 2.41 2.63 2.41 4.42v3.72a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3.72c0-1.79.85-3.5 2.41-4.42C48.354 39.28 52 33.01 52 26c0-11.046-8.954-20-20-20Z"
    />
    <path
      className="light-bulb-highlight"
      d="M24 18c2.667-3.333 6.667-5 12-5"
      strokeLinecap="round"
      strokeWidth={3}
    />
    <path
      className="light-bulb-filament"
      d="M24 36c3 0 4 4 8 4s5-4 8-4"
      strokeLinecap="round"
      strokeWidth={4}
    />
    <path
      className="light-bulb-filament"
      d="M26 40h12"
      strokeLinecap="round"
      strokeWidth={3}
    />
    <rect className="light-bulb-base" x="24" y="45" width="16" height="5" rx="2.5" />
    <rect className="light-bulb-base" x="22" y="50" width="20" height="5" rx="2.5" />
    <rect className="light-bulb-base" x="26" y="55" width="12" height="5" rx="2.5" />
  </svg>
);
