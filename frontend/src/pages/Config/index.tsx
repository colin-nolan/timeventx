import RefreshIcon from "@mui/icons-material/Refresh";
import WarningIcon from "@mui/icons-material/Warning";
import { Button, ButtonGroup, Textarea } from "@mui/joy";
import Typography from "@mui/joy/Typography";
import { useEffect, useState } from "preact/compat";
import { toast } from "sonner";
import { ApiClient } from "../../lib/api-client";

export function Config(props: { apiRootUrl: string }) {
    const [config, setConfig] = useState<string>("");
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
        apiClient
            .getConfig()
            .then((config: object) => {
                setConfig(JSON.stringify(config, null, 4));
            })
            .catch((error: string) => {
                toast.error(error);
            });
    }, [apiClient]);

    return (
        <>
            <Typography level="h1">Config</Typography>
            <Textarea minRows={20} value={config} />
        </>
    );
}
