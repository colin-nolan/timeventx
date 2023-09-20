import WarningIcon from "@mui/icons-material/Warning";
import { Button } from "@mui/joy";
import Typography from "@mui/joy/Typography";
import { useEffect, useState } from "preact/compat";
import { toast } from "sonner";
import { ApiClient } from "../../lib/api-client";

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
                O;
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
            <Typography level="h1">Reset</Typography>
            <Button color="danger" startDecorator={<WarningIcon />} onClick={reset} loading={resetting}>
                Reset Device
            </Button>
        </>
    );
}
