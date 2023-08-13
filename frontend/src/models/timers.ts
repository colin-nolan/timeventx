interface DayTime {
    hour: number;
    minute: number;
    second: number;
}

type TimerId = number;

interface Timer {
    id?: TimerId;
    name: string;
    startTime: DayTime;
    durationInSeconds: number;
}
