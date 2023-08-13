import "./style.css";
import { useEffect, useState } from "preact/compat";

import { Table } from "@mui/joy";
import React from "react";
import { toast } from "sonner";
import { TimerRow } from "../../components/TimerRow";
import { TimerCreationRow } from "../../components/TimerCreationRow";

// const API_ROOT = "http://192.168.0.156:8080/api/v1";
const API_ROOT = "http://0.0.0.0:8080/api/v1";

export function Home() {
    const [timers, setTimers] = useState<Timer[]>([]);

    function addTimer(timer: Timer, onSuccess: () => void, onFail: () => void) {
        fetch(`${API_ROOT}/timer`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(timer),
        }).then(async (response) => {
            if (!response.ok) {
                console.error(`Server did not create timer`, response);
                toast.error(`Problem creating timer (${response.status})`);
                onFail();
            } else {
                const timer = await response.json();
                setTimers([...timers, timer]);
                onSuccess();
            }
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
                    <TimerCreationRow addTimer={addTimer} />
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
