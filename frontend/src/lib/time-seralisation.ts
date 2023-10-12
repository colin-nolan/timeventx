export function secondsToHhmmss(duration: number): string {
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;
    return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${seconds
        .toString()
        .padStart(2, "0")}`;
}

export function hhmmssToSeconds(dayTime: string): number {
    const [hours, minutes, seconds] = dayTime.split(":").map((s) => parseInt(s));
    return hours * 3600 + minutes * 60 + seconds;
}
