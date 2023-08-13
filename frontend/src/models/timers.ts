type TimerId = number;
type Second = number;

interface Timer {
    id?: TimerId;
    name: string;
    startTime: string;
    duration: Second;
}
