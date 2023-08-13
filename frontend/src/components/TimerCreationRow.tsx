import { useState } from "preact/compat";
import { Button, Input } from "@mui/joy";
import React from "react";

type CreateTimer = (timer: Timer, onSuccess: () => void, onFail: () => void) => void;

export function TimerCreationRow(props: { addTimer: CreateTimer; timer?: Timer }) {
    const [name, setName] = useState<string>(props.timer ? props.timer.name : "");
    const [startTime, setStartTime] = useState<string>(props.timer ? props.timer.startTime : "00:00:00");
    const [duration, setDuration] = useState<Second>(props.timer ? props.timer.duration : 1);

    function addTimer(event: Event) {
        props.addTimer(
            {
                id: null,
                name: name,
                startTime: startTime,
                duration: duration,
            },
            onSuccess,
            onFail,
        );
    }

    function onSuccess() {}

    function onFail() {}

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
                />
            </td>
            <td>
                <Input
                    type="time"
                    onChange={(event) => setStartTime(event.target.value)}
                    value={startTime}
                    placeholder="12:00:00"
                />
            </td>
            <td>
                <Input
                    type="number"
                    onChange={(event) => setDuration(Number(event.target.value))}
                    value={duration}
                    slotProps={{ input: { min: 1, max: 60 * 60 * 24 } }}
                />
            </td>
            <td>
                <Button onClick={addTimer} style={{ width: "100%" }}>
                    Add
                </Button>
            </td>
        </tr>
    );
}
