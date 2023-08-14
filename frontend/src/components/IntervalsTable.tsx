import { useEffect, useState } from "preact/compat";

import { Button, Table } from "@mui/joy";
import React from "react";
import { TimerRow } from "./TimerRow";
import { TimerCreationRow } from "./TimerCreationRow";
import { Add } from "@mui/icons-material";
import { ApiClient, Interval, Timer, TimerId, TimersClient } from "../lib/api-client";
import { toast } from "sonner";

function dayTimeToSeconds(dayTime: string): number {
    const [hours, minutes, seconds] = dayTime.split(":").map((s) => parseInt(s));
    return hours * 3600 + minutes * 60 + seconds;
}

export function IntervalsTable(props: { apiRootUrl: string; timers?: Timer[] }) {
    const [apiClient, setApiClient] = useState<ApiClient>(new ApiClient(props.apiRootUrl));
    const [intervals, setIntervals] = useState<Interval[]>([]);

    useEffect(() => {
        // Stop double setting at start, and avoid having to handle `null`
        if (apiClient.apiRootUrl !== props.apiRootUrl) {
            setApiClient(new ApiClient(props.apiRootUrl));
        }
    }, [props.apiRootUrl]);

    useEffect(() => {
        updateIntervals();
    }, [apiClient, props.timers]);

    function updateIntervals() {
        apiClient
            .getIntervals()
            .then((intervals) => {
                setIntervals(intervals);
            })
            .catch((error) => {
                toast.error(error);
            });
    }

    return (
        <Table aria-label="basic table" size="lg" stickyHeader>
            <thead>
                <tr>
                    <th>Start Time</th>
                    <th>End Time</th>
                </tr>
            </thead>
            <tbody>
                {intervals
                    .sort(
                        (interval1, interval2) =>
                            dayTimeToSeconds(interval1.startTime) - dayTimeToSeconds(interval2.startTime),
                    )
                    .map((interval) => (
                        <tr>
                            <td>{interval.startTime}</td>
                            <td>{interval.endTime}</td>
                        </tr>
                    ))}
            </tbody>
        </Table>
    );
}
