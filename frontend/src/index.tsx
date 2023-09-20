import CssBaseline from "@mui/joy/CssBaseline";
import { Sheet, CssVarsProvider, Link } from "@mui/joy";
import { render } from "preact";
import { LocationProvider, Route, Router, useLocation } from "preact-iso";
import { Header } from "./components/Header";
import { JoyToaster } from "./components/JoyToaster";
import { Timers } from "./pages/Timers";
import { Logs } from "./pages/Logs";
import { Reset } from "./pages/Reset";
import { Stats } from "./pages/Stats";
import { NotFound } from "./pages/_404";

// TODO: configure
// const API_ROOT = "http://192.168.0.156:8080/api/v1";
const API_ROOT = "http://0.0.0.0:8080/api/v1";

export function App() {
    return (
        <LocationProvider>
            <CssVarsProvider>
                <CssBaseline />

                <JoyToaster />

                <Sheet variant="outlined" style={{ minHeight: "100vh" }}>
                    <Header />

                    <main style={{ margin: "20px 20px 0 20px" }}>
                        <Router>
                            <Route default path="/" component={Timers} apiRootUrl={API_ROOT} />
                            <Route path="/logs" component={Logs} apiRootUrl={API_ROOT} />
                            <Route path="/stats" component={Stats} apiRootUrl={API_ROOT} />
                            <Route path="/reset" component={Reset} apiRootUrl={API_ROOT} />
                            <Route default component={NotFound} />
                        </Router>
                    </main>
                </Sheet>
            </CssVarsProvider>
        </LocationProvider>
    );
}

render(<App />, document.getElementById("app"));
