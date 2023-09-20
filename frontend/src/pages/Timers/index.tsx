import Typography from "@mui/joy/Typography";
import { useState } from "preact/compat";
import { IntervalsTable } from "../../components/IntervalsTable";
import { TimersTable } from "../../components/TimersTable";
import { Timer } from "../../lib/api-client";

export function Timers(props: { apiRootUrl: string }) {
    const [timers, setTimers] = useState<Timer[]>([]);

    return (
        <>
            <Typography level="h1">Timers</Typography>
            <TimersTable apiRootUrl={props.apiRootUrl} onTimersChange={setTimers} />

            <Typography level="h1">Intervals</Typography>
            <IntervalsTable apiRootUrl={props.apiRootUrl} timers={timers} />
        </>
    );
}
