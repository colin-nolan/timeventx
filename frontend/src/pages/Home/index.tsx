import "./style.css";
import { useEffect, useState } from "preact/compat";

import { Button, Input, Table } from "@mui/joy";
import React from "react";
import { toast } from "sonner";
import { TimerRow } from "../../components/TimerRow";

// const API_ROOT = "http://192.168.0.156:8080/api/v1";
const API_ROOT = "http://0.0.0.0:8080/api/v1";

export function Home() {
    const [timers, setTimers] = useState<Timer[]>([]);

    const [name, setName] = useState<string>("");
    // FIXME: use DayTime
    const [startTime, setStartTime] = useState<string>("00:00:00");
    const [durationInSeconds, setDurationInSeconds] = useState<number>(1);

    function addTimer() {
        // TODO
        // const [hours, minutes, seconds] = startTime.split(":")

        fetch(`${API_ROOT}/timer`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                name: name,
                start_time: startTime,
                duration: durationInSeconds,
            }),
        }).then(async (response) => {
            const timer = await response.json();
            setTimers([...timers, timer]);
        });
    }

    function removeTimer(timerId: TimerId, onSuccess: () => void, onFail: () => void) {
        fetch(`${API_ROOT}/timer`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(timerId),
        })
            .then(async (response) => {
                if (!response.ok) {
                    console.error(`Server did not remove timer: ${timerId}`, response);
                    toast.error(`Problem removing timer (${response.status})`);
                    onFail();
                } else {
                    setTimers(timers.filter((timer) => timer.id !== timerId));
                    onSuccess();
                }
            })
            .catch((error) => {
                console.error(`Error communicating with server for removal of timer: ${timerId}`, error);
                toast.error(`Problem removing timer (${error})`);
                onFail();
            });
    }

    useEffect(() => {
        fetch(`${API_ROOT}/timers`).then(async (response) => {
            const timers = await response.json();
            setTimers(timers);
        });
    }, []);

    return (
        <>
            <Table aria-label="basic table" size="lg" stickyHeader hoverRow>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Start Time</th>
                        <th>Duration (s)</th>
                        <th aria-label="last" style={{ width: "var(--Table-lastColumnWidth)" }} />
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <Input disabled value="Auto" />
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
                                onChange={(event) => setDurationInSeconds(Number(event.target.value))}
                                value={durationInSeconds}
                                slotProps={{ input: { min: 1, max: 60 * 60 * 24 } }}
                            />
                        </td>
                        <td>
                            <Button onClick={addTimer} style={{ width: "100%" }}>
                                Add
                            </Button>
                        </td>
                    </tr>
                    {timers
                        .sort((timer_1, timer_2) => timer_1.id - timer_2.id)
                        .map((timer) => {
                            return <TimerRow timer={timer} removeTimer={removeTimer} />;
                        })}
                </tbody>
            </Table>
        </>
    );
}
