import "./style.css";
import React from "react";
import { TimersTable } from "../../components/TimersTable";

export function Home(props: { apiRootUrl: string }) {
    return (
        <>
            <h1>Timers</h1>
            <TimersTable apiRootUrl={props.apiRootUrl} />
        </>
    );
}
