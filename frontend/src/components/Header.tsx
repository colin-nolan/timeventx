import List from "@mui/joy/List";
import ListDivider from "@mui/joy/ListDivider";
import ListItem from "@mui/joy/ListItem";
import ListItemButton from "@mui/joy/ListItemButton";
import Sheet from "@mui/joy/Sheet";
import { useLocation } from "preact-iso";

function NavListItem({ title, link }) {
    return (
        <ListItem role="none">
            <ListItemButton role="menuitem" component="a" href={link} style={{ fontWeight: "bold" }}>
                {title}
            </ListItemButton>
        </ListItem>
    );
}

export function Header() {
    const { url } = useLocation();

    return (
        <header>
            <Sheet
                variant="soft"
                component="nav"
                style={{ display: "flex", justifyContent: "center", alignItems: "center" }}
            >
                <div>
                    <List
                        role="menubar"
                        orientation="horizontal"
                        sx={{
                            "--List-radius": "8px",
                            "--List-paddingX": "8px",
                            "--List-gap": "8px",
                            "--ListItem-paddingX": "5vw",
                        }}
                        style={{ marginLeft: "8px" }}
                    >
                        <NavListItem title="Timers" link="/" />
                        <ListDivider />
                        <NavListItem title="Logs" link="/logs" />
                        <ListDivider />
                        <NavListItem title="Stats" link="/stats" />
                        <ListDivider />
                        <NavListItem title="Reset" link="/reset" />
                    </List>
                </div>
            </Sheet>
        </header>
    );
}
