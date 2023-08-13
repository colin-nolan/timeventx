import "./style.css";
import { useEffect, useState } from "preact/compat";

import { Button, Input, Table, ButtonGroup } from "@mui/joy";
import ReportIcon from "@mui/icons-material/Report";
import WarningIcon from "@mui/icons-material/Warning";
import React from "react";
import { toast } from "sonner";

// const API_ROOT = "http://192.168.0.156:8080/api/v1";
const API_ROOT = "http://0.0.0.0:8080/api/v1";

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

export function Home() {
    const [timers, setTimers] = useState<Timer[]>([]);

    const [timersConfirmingRemoval, setTimersConfirmingRemoval] = useState<Set<TimerId>>(new Set());
    const [timersBeingRemoved, setTimersBeingRemoved] = useState<Set<TimerId>>(new Set());
    const [timersConfirmingFailure, setTimersConfirmingFailure] = useState<Set<TimerId>>(new Set());

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

    function removeTimer(timerId: TimerId) {
        setTimersBeingRemoved(new Set(timersBeingRemoved.add(timerId)));
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
                    setTimersConfirmingFailure(new Set(timersConfirmingFailure.add(timerId)));
                } else {
                    setTimers(timers.filter((timer) => timer.id !== timerId));
                    timersConfirmingRemoval.delete(timerId);
                    setTimersConfirmingRemoval(new Set(timersConfirmingRemoval));
                }
            })
            .catch((error) => {
                console.error(`Error communicating with server for removal of timer: ${timerId}`, error);
                toast.error(`Problem removing timer (${error})`);
                setTimersConfirmingFailure(new Set(timersConfirmingFailure.add(timerId)));
            })
            .finally(() => {
                timersBeingRemoved.delete(timerId);
                setTimersBeingRemoved(new Set(timersBeingRemoved));
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
                            return (
                                <tr
                                    style={{
                                        backgroundColor: timersConfirmingRemoval.has(timer.id)
                                            ? "var(--joy-palette-danger-50, #FEF6F6)"
                                            : null,
                                    }}
                                >
                                    <>
                                        <td>{timer.id}</td>
                                        <td>{timer.name}</td>
                                        <td>{timer.startTime}</td>
                                        <td>{timer.durationInSeconds}</td>
                                        <td>
                                            {timersConfirmingRemoval.has(timer.id) ? (
                                                <ButtonGroup spacing={1} buttonFlex={1} variant="soft">
                                                    <Button
                                                        color="danger"
                                                        style={{ width: "50%" }}
                                                        loading={timersBeingRemoved.has(timer.id)}
                                                        onClick={() => {
                                                            removeTimer(timer.id);
                                                        }}
                                                        startDecorator={
                                                            timersConfirmingFailure.has(timer.id) ? (
                                                                <ReportIcon />
                                                            ) : (
                                                                <WarningIcon />
                                                            )
                                                        }
                                                    >
                                                        {timersConfirmingFailure.has(timer.id)
                                                            ? "Retry Removal"
                                                            : "Confirm Removal"}
                                                    </Button>
                                                    <Button
                                                        style={{ width: "50%" }}
                                                        color="primary"
                                                        disabled={timersBeingRemoved.has(timer.id)}
                                                        onClick={() => {
                                                            timersConfirmingRemoval.delete(timer.id);
                                                            setTimersConfirmingRemoval(
                                                                new Set(timersConfirmingRemoval),
                                                            );
                                                            if (timersConfirmingFailure.has(timer.id)) {
                                                                timersConfirmingFailure.delete(timer.id);
                                                                setTimersConfirmingFailure(
                                                                    new Set(timersConfirmingFailure),
                                                                );
                                                            }
                                                        }}
                                                    >
                                                        Cancel
                                                    </Button>
                                                </ButtonGroup>
                                            ) : (
                                                <ButtonGroup spacing={1} buttonFlex={1} variant="soft">
                                                    <Button color="primary" style={{ width: "50%" }}>
                                                        Edit
                                                    </Button>
                                                    <Button
                                                        color="danger"
                                                        onClick={() => {
                                                            setTimersConfirmingRemoval(
                                                                new Set(timersConfirmingRemoval.add(timer.id)),
                                                            );
                                                        }}
                                                        style={{ width: "50%" }}
                                                    >
                                                        Delete
                                                    </Button>
                                                </ButtonGroup>
                                            )}
                                        </td>
                                    </>
                                </tr>
                            );
                        })}
                </tbody>
            </Table>
        </>
    );
}
