import RefreshIcon from "@mui/icons-material/Refresh";
import { Button, ButtonGroup, Textarea } from "@mui/joy";
import Typography from "@mui/joy/Typography";
import { useEffect, useState } from "preact/compat";
import { toast } from "sonner";
import { ApiClient } from "../../lib/api-client";

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
            <Typography level="h1">Stats</Typography>
            <ButtonGroup spacing={1} buttonFlex={1} variant="soft">
                <Button startDecorator={<RefreshIcon />} onClick={refreshStats} loading={refreshingStats}>
                    Reload
                </Button>
            </ButtonGroup>
            <Textarea minRows={20} value={stats} />
        </>
    );
}
