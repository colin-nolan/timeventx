import React from "react";
import { useEffect, useState } from "preact/compat";
import { Button, ButtonGroup, Textarea } from "@mui/joy";
import { ApiClient } from "../../lib/api-client";
import { toast } from "sonner";
import RefreshIcon from "@mui/icons-material/Refresh";
import WarningIcon from "@mui/icons-material/Warning";

export function Reset(props: { apiRootUrl: string }) {
    const [resetting, setResetting] = useState<boolean>(false);
    const [apiClient, setApiClient] = useState<ApiClient>(new ApiClient(props.apiRootUrl));

    useEffect(() => {
        // Stop double setting at start, and avoid having to handle `null`
        if (apiClient.apiRootUrl !== props.apiRootUrl) {
            setApiClient(new ApiClient(props.apiRootUrl));
        }
    }, [props.apiRootUrl]);

    function reset() {
        setResetting(true);
        apiClient
            .resetDevice()
            .then(() => {
                toast.success("Device reset");
            })
            .catch((error) => {
                toast.error("Failed to reset device");
            })
            .finally(() => {
                setResetting(false);
            });
    }

    return (
        <>
            <h1>Reset</h1>
            <Button color="danger" startDecorator={<WarningIcon />} onClick={reset} loading={resetting}>
                Reset Device
            </Button>
        </>
    );
}
