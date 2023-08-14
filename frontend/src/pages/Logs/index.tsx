import React from "react";
import { useEffect, useState } from "preact/compat";
import { Button, ButtonGroup, Textarea } from "@mui/joy";
import { ApiClient } from "../../lib/api-client";
import { toast } from "sonner";
import RefreshIcon from "@mui/icons-material/Refresh";
import WarningIcon from "@mui/icons-material/Warning";

export function Logs(props: { apiRootUrl: string }) {
    const [logs, setLogs] = useState<string>("");
    const [refreshingLogs, setRefreshingLogs] = useState<boolean>(false);
    const [apiClient, setApiClient] = useState<ApiClient>(new ApiClient(props.apiRootUrl));
    const [confirmingClear, setConfirmingClear] = useState<boolean>(false);

    useEffect(() => {
        // Stop double setting at start, and avoid having to handle `null`
        if (apiClient.apiRootUrl !== props.apiRootUrl) {
            setApiClient(new ApiClient(props.apiRootUrl));
        }
    }, [props.apiRootUrl]);

    useEffect(() => {
        refreshLogs();
    }, [apiClient]);

    function refreshLogs() {
        setRefreshingLogs(true);
        apiClient
            .getLogs()
            .then((logs: string) => {
                setLogs(logs);
            })
            .catch((error: string) => {
                toast.error(error);
            })
            .finally(() => {
                setRefreshingLogs(false);
            });
    }

    function clearLogs() {
        setRefreshingLogs(true);
        apiClient
            .clearLogs()
            .then(() => {
                setConfirmingClear(false);
                refreshLogs();
            })
            .catch((error: string) => {
                toast.error(error);
            });
    }

    return (
        <>
            <h1>Logs</h1>
            <ButtonGroup spacing={1} buttonFlex={1} variant="soft">
                <Button startDecorator={<RefreshIcon />} onClick={refreshLogs} loading={refreshingLogs}>
                    Reload
                </Button>
                <Button
                    color="danger"
                    startDecorator={<WarningIcon />}
                    onClick={() => (!confirmingClear ? setConfirmingClear(true) : clearLogs())}
                >
                    {confirmingClear ? "Confirm Clear?" : "Clear"}
                </Button>
            </ButtonGroup>
            <Textarea minRows={20} value={logs} />
        </>
    );
}
