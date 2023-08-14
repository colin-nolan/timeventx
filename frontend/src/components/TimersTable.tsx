import { useEffect, useState } from "preact/compat";

import { Button, Table } from "@mui/joy";
import React from "react";
import { TimerRow } from "./TimerRow";
import { TimerCreationRow } from "./TimerCreationRow";
import { Add } from "@mui/icons-material";
import { Timer, TimerId, TimersClient } from "../lib/api-client";
import { toast } from "sonner";

export function TimersTable(props: { apiRootUrl: string }) {
    const [timers, setTimers] = useState<Timer[]>([]);
    const [creatingTimer, setCreatingTimer] = useState<boolean>(false);

    const [timersClient, setTimersClient] = useState<TimersClient>(new TimersClient(props.apiRootUrl));

    useEffect(() => {
        // Stop double setting at start, and avoid having to handle `null`
        if (timersClient.apiRootUrl !== props.apiRootUrl) {
            setTimersClient(new TimersClient(props.apiRootUrl));
        }
    }, [props.apiRootUrl]);

    useEffect(() => {
        timersClient
            .getTimers()
            .then((timers) => {
                setTimers(timers);
            })
            .catch((error) => {
                toast.error(error);
            });
    }, [timersClient]);

    function addTimer(timer: Timer, onSuccess: () => void, onFail: () => void) {
        const updatingTimer = Boolean(timer.id);

        timersClient
            .addOrUpdateTimer(timer)
            .then((addedTimer) => {
                let updated_timers: Timer[];
                if (updatingTimer) {
                    updated_timers = timers.filter((t) => t.id !== addedTimer.id);
                    updated_timers.push(addedTimer);
                } else {
                    updated_timers = [...timers, addedTimer];
                }
                setTimers(updated_timers);
                onSuccess();
            })
            .catch((error) => {
                toast.error(error);
                onFail();
            });
    }

    function removeTimer(timerId: TimerId, onSuccess: () => void, onFail: () => void) {
        timersClient
            .removeTimer(timerId)
            .then(() => {
                setTimers(timers.filter((timer) => timer.id !== timerId));
                onSuccess();
            })
            .catch((error) => {
                toast.error(error);
                onFail();
            });
    }

    return (
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
                        {/*
                         * FIXME: CSS
                         */}
                        <td colSpan={5} style={{ textAlign: "center" }} class="no-hover-background-change">
                            <Button
                                startDecorator={<Add />}
                                style={{ width: "75%" }}
                                variant="outlined"
                                onClick={() => setCreatingTimer(true)}
                            >
                                Create Timer
                            </Button>
                        </td>
                    </tr>
                )}
            </tbody>
        </Table>
    );
}
