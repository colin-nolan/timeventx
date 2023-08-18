export function secondsToHoursAndMinutes(duration: number): string {
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
}

export function hhmmssToSeconds(dayTime: string): number {
    const [hours, minutes, seconds] = dayTime.split(":").map((s) => parseInt(s));
    return hours * 3600 + minutes * 60 + seconds;
}

export function mmssToSeconds(time: string): number {
    const [minutes, seconds] = time.split(":").map((s) => Number(s));
    return minutes * 60 + seconds;
}
