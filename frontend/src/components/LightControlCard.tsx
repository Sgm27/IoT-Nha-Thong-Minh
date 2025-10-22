import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LightBulbIcon } from "@/components/icons/LightBulbIcon";
import { cn } from "@/lib/utils";
import { normalizeLocation } from "@/lib/lights";
import type { LightState } from "@/types/smart-home";

interface LightControlCardProps {
  lights: LightState[];
  lightLocation: string;
  onLightLocationChange: (value: string) => void;
  onLightAction: (action: "on" | "off") => void;
}

export function LightControlCard({ lights, lightLocation, onLightLocationChange, onLightAction }: LightControlCardProps) {
  const hasLights = lights.length > 0;

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle>Quản lý đèn</CardTitle>
        <CardDescription>Theo dõi trạng thái đèn và gửi lệnh bật/tắt tức thời.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-1 flex-col gap-6">
        <form className="grid grid-cols-1 gap-4 sm:grid-cols-[1fr_auto] sm:items-end" onSubmit={(event) => event.preventDefault()}>
          <div className="space-y-2 sm:col-span-1">
            <Label htmlFor="light-location">Vị trí đèn</Label>
            <Input
              id="light-location"
              value={lightLocation}
              onChange={(event) => onLightLocationChange(event.target.value)}
              placeholder="Ví dụ: phòng khách"
            />
          </div>
          <div className="flex flex-col gap-2 sm:col-span-1 sm:flex-row">
            <Button type="button" className="flex-1" onClick={() => onLightAction("on")}>
              Bật đèn
            </Button>
            <Button type="button" variant="secondary" className="flex-1" onClick={() => onLightAction("off")}>
              Tắt đèn
            </Button>
          </div>
        </form>

        <div className="space-y-3">
          <h3 className="text-lg font-semibold">Trạng thái các đèn</h3>
          {hasLights ? (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
              {lights.map((light) => (
                <div
                  key={normalizeLocation(light.location)}
                  className={cn(
                    "light-card group relative flex flex-col items-center gap-3 rounded-2xl border bg-gradient-to-br p-4 text-center shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-lg",
                    light.is_on
                      ? "from-yellow-50/80 via-amber-50/60 to-amber-100/40 border-yellow-200/80 shadow-[0_18px_40px_-25px_rgba(250,204,21,0.85)] dark:from-amber-500/20 dark:via-amber-500/10 dark:to-amber-500/5 dark:border-amber-400/60"
                      : "from-slate-100/80 via-slate-100/60 to-slate-200/40 border-slate-200/80 shadow-[0_16px_38px_-28px_rgba(15,23,42,0.85)] dark:from-slate-800/70 dark:via-slate-900/60 dark:to-slate-900/40 dark:border-slate-700/60"
                  )}
                >
                  <LightBulbIcon isOn={light.is_on} />
                  <div className="space-y-1">
                    <p className="text-sm font-semibold tracking-wide text-foreground">{light.location}</p>
                    <p className="text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
                      {light.is_on ? "Đang bật" : "Đang tắt"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex min-h-[140px] flex-col items-center justify-center rounded-2xl border border-dashed bg-muted/40 p-6 text-center text-sm text-muted-foreground">
              Chưa có dữ liệu
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
