import { Button, ButtonGroup, Input } from "@mui/joy";
import { useState } from "preact/compat";
import { Second, Timer } from "../lib/api-client";
import { mmssToSeconds, secondsToHoursAndMinutes } from "../lib/time-seralisation";

export type AddTimer = (timer: Timer, onSuccess: () => void, onFail: () => void) => void;

export function TimerCreationRow(props: { addTimer: AddTimer; timer?: Timer; onClose?: () => void }) {
    const [name, setName] = useState<string>(props.timer ? props.timer.name : "");
    const [startTime, setStartTime] = useState<string>(props.timer ? props.timer.startTime : "00:00:00");
    const [duration, setDuration] = useState<Second>(props.timer ? props.timer.duration : 1);

    const [beingCreated, setBeingCreated] = useState<boolean>(false);

    function addTimer() {
        setBeingCreated(true);
        props.addTimer(
            {
                id: props.timer ? props.timer.id : null,
                name: name,
                startTime: startTime,
                duration: duration,
            },
            onSuccess,
            onFail,
        );
    }

    function onSuccess() {
        setBeingCreated(false);
        if (props.onClose) {
            props.onClose();
        }
    }

    function onFail() {
        setBeingCreated(false);
    }

    return (
        <tr>
            <td>
                <Input disabled value={props.timer ? props.timer.id : "Auto"} />
            </td>
            <td>
                <Input
                    type="string"
                    onChange={(event) => setName(event.target.value)}
                    value={name}
                    placeholder="Name"
                    slotProps={{
                        input: {
                            "data-testid": "timer-name"
                        }
                    }}
                />
            </td>
            <td>
                <Input
                    type="time"
                    onChange={(event) => setStartTime(event.target.value)}
                    value={startTime}
                    placeholder="12:00:00"
                    slotProps={{
                        input: {
                            "data-testid": "timer-start-time"
                        }
                    }}
                />
            </td>
            <td>
                <Input
                    type="time"
                    onChange={(event) => setDuration(mmssToSeconds(event.target.value))}
                    value={secondsToHoursAndMinutes(duration)}
                    slotProps={{
                        input: {
                            "data-testid": "timer-duration"
                        }
                    }}
                />
            </td>
            <td>
                <ButtonGroup spacing={1} buttonFlex={1} variant="solid">
                    <Button
                        style={{ width: "50%" }}
                        onClick={addTimer}
                        loading={beingCreated}
                        color="success"
                        data-testid="timer-add-button"
                    >
                        {props.timer ? "Complete" : "Add"}
                    </Button>
                    <Button
                        style={{ width: "50%" }}
                        onClick={props.onClose}
                        color="neutral"
                        data-testid="timer-create-cancel-button"
                    >
                        Cancel
                    </Button>
                </ButtonGroup>
            </td>
        </tr>
    );
}
