import { useLocation } from "preact-iso";
import React from "react";
import { Link } from "@mui/joy";

export function Header() {
    const { url } = useLocation();

    return (
        <header>
            <nav>
                <Link href="/">Home</Link>
                <Link href="/logs">Logs</Link>
                <Link href="/stats">Stats</Link>
                <Link href="/reset">Reset</Link>
            </nav>
        </header>
    );
}
