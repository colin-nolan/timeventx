import { useState } from "preact/compat";
import { Button, ButtonGroup } from "@mui/joy";
import ReportIcon from "@mui/icons-material/Report";
import WarningIcon from "@mui/icons-material/Warning";
import React from "react";
import { AddTimer, TimerCreationRow } from "./TimerCreationRow";
import { Timer, TimerId } from "../lib/api-client";
import { secondsToHoursAndMinutes } from "../lib/time-seralisation";

type RemoveTimer = (timerId: TimerId, onSuccess: () => void, onFail: () => void) => void;

export function TimerRow(props: { timer: Timer; removeTimer: RemoveTimer; addTimer: AddTimer }) {
    const [timerConfirmingRemoval, setTimerConfirmingRemoval] = useState<boolean>(false);
    const [timerBeingRemoved, setTimerBeingRemoved] = useState<boolean>(false);
    const [timerConfirmingFailure, setTimerConfirmingFailure] = useState<boolean>(false);
    const [timerEditing, setTimerEditing] = useState<boolean>(false);

    function removeTimer(event: Event) {
        setTimerBeingRemoved(true);
        props.removeTimer(props.timer.id, reset, timerRemovalFailed);
    }

    function startTimerRemoval(event: Event) {
        setTimerConfirmingRemoval(true);
    }

    function reset() {
        setTimerConfirmingRemoval(false);
        setTimerBeingRemoved(false);
        setTimerConfirmingFailure(false);
        setTimerEditing(false);
    }

    function timerRemovalFailed() {
        setTimerBeingRemoved(false);
        setTimerConfirmingFailure(true);
    }

    return !timerEditing ? (
        <tr
            style={{
                backgroundColor: timerConfirmingRemoval ? "var(--joy-palette-danger-50, #FEF6F6)" : null,
            }}
        >
            <td>{props.timer.id}</td>
            <td>{props.timer.name}</td>
            <td>{props.timer.startTime}</td>
            <td>{secondsToHoursAndMinutes(props.timer.duration)}</td>
            <td>
                {timerConfirmingRemoval ? (
                    <ButtonGroup spacing={1} buttonFlex={1} variant="solid">
                        <Button
                            color="danger"
                            style={{ width: "50%" }}
                            loading={timerBeingRemoved}
                            onClick={removeTimer}
                            startDecorator={timerConfirmingFailure ? <ReportIcon /> : <WarningIcon />}
                        >
                            {timerConfirmingFailure ? "Retry Removal" : "Confirm Removal"}
                        </Button>
                        <Button color="neutral" style={{ width: "50%" }} disabled={timerBeingRemoved} onClick={reset}>
                            Cancel
                        </Button>
                    </ButtonGroup>
                ) : (
                    <ButtonGroup spacing={1} buttonFlex={1} variant="soft">
                        <Button color="primary" style={{ width: "50%" }} onClick={() => setTimerEditing(true)}>
                            Edit
                        </Button>
                        <Button color="danger" onClick={startTimerRemoval} style={{ width: "50%" }}>
                            Delete
                        </Button>
                    </ButtonGroup>
                )}
            </td>
        </tr>
    ) : (
        <TimerCreationRow addTimer={props.addTimer} timer={props.timer} onClose={() => setTimerEditing(false)} />
    );
}
