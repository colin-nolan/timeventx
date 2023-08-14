import "./style.css";
import React from "react";
import { TimersTable } from "../../components/TimersTable";
import { IntervalsTable } from "../../components/IntervalsTable";
import { useEffect, useState } from "preact/compat";
import { ApiClient, Interval, Timer } from "../../lib/api-client";
import { toast } from "sonner";

export function Home(props: { apiRootUrl: string }) {
    const [timers, setTimers] = useState<Timer[]>([]);

    return (
        <>
            <h1>Timers</h1>
            <TimersTable apiRootUrl={props.apiRootUrl} onTimersChange={setTimers} />

            <h1>Intervals</h1>
            <IntervalsTable apiRootUrl={props.apiRootUrl} timers={timers} />
        </>
    );
}
