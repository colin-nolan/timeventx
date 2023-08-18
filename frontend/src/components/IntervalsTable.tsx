import { useEffect, useState } from "preact/compat";

import { Table } from "@mui/joy";
import React from "react";
import { ApiClient, Interval, Timer } from "../lib/api-client";
import { toast } from "sonner";
import { hhmmssToSeconds } from "../lib/time-seralisation";

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
                            hhmmssToSeconds(interval1.startTime) - hhmmssToSeconds(interval2.startTime),
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
