import "./style.css";
import { useEffect, useState } from "preact/compat";

import { Button, Table } from "@mui/joy";
import React from "react";
import { toast } from "sonner";
import { TimerRow } from "../../components/TimerRow";
import { TimerCreationRow } from "../../components/TimerCreationRow";

// const API_ROOT = "http://192.168.0.156:8080/api/v1";
const API_ROOT = "http://0.0.0.0:8080/api/v1";

export function Home() {
    const [timers, setTimers] = useState<Timer[]>([]);
    const [creatingTimer, setCreatingTimer] = useState<boolean>(false);

    function addTimer(timer: Timer, onSuccess: () => void, onFail: () => void) {
        const updating_timer = Boolean(timer.id);
        const url_suffix = updating_timer ? `/${timer.id}` : "";

        fetch(`${API_ROOT}/timer${url_suffix}`, {
            method: updating_timer ? "PUT" : "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(timer),
        }).then(async (response) => {
            if (!response.ok) {
                const reason = await response.text();
                console.error(`Server did not process timer: ${reason}`, response);
                toast.error(`Problem ${updating_timer ? "updating" : "creating"} timer (${response.status})`);
                onFail();
            } else {
                const added_timer = await response.json();
                let updated_timers: Timer[];
                if (updating_timer) {
                    updated_timers = timers.filter((t) => t.id !== added_timer.id);
                    updated_timers.push(added_timer);
                } else {
                    updated_timers = [...timers, added_timer];
                }
                setTimers(updated_timers);
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
                    {timers
                        .sort((timer_1, timer_2) => timer_1.id - timer_2.id)
                        .map((timer) => {
                            return <TimerRow timer={timer} removeTimer={removeTimer} addTimer={addTimer} />;
                        })}
                    {creatingTimer ? (
                        <TimerCreationRow addTimer={addTimer} onClose={() => setCreatingTimer(false)} />
                    ) : (
                        <tr>
                            <td colSpan={5} style={{ textAlign: "center" }}>
                                <Button onClick={() => setCreatingTimer(true)}>Create Timer</Button>
                            </td>
                        </tr>
                    )}
                </tbody>
            </Table>
        </>
    );
}
