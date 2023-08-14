import React from "react";
import { useEffect, useState } from "preact/compat";
import { Button, ButtonGroup, Textarea } from "@mui/joy";
import { ApiClient } from "../../lib/api-client";
import { toast } from "sonner";
import RefreshIcon from "@mui/icons-material/Refresh";
import WarningIcon from "@mui/icons-material/Warning";

export function Stats(props: { apiRootUrl: string }) {
    const [stats, setStats] = useState<string>("");
    const [refreshingStats, setRefreshingStats] = useState<boolean>(false);
    const [apiClient, setApiClient] = useState<ApiClient>(new ApiClient(props.apiRootUrl));

    useEffect(() => {
        // Stop double setting at start, and avoid having to handle `null`
        if (apiClient.apiRootUrl !== props.apiRootUrl) {
            setApiClient(new ApiClient(props.apiRootUrl));
        }
    }, [props.apiRootUrl]);

    useEffect(() => {
        refreshStats();
    }, [apiClient]);

    function refreshStats() {
        setRefreshingStats(true);
        apiClient
            .getStats()
            .then((logs: string) => {
                setStats(logs);
            })
            .catch((error: string) => {
                toast.error(error);
            })
            .finally(() => {
                setRefreshingStats(false);
            });
    }

    return (
        <>
            <h1>Stats</h1>
            <ButtonGroup spacing={1} buttonFlex={1} variant="soft">
                <Button startDecorator={<RefreshIcon />} onClick={refreshStats} loading={refreshingStats}>
                    Reload
                </Button>
            </ButtonGroup>
            <Textarea minRows={20} value={stats} />
        </>
    );
}
