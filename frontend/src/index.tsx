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
import { BACKEND_API_ROOT } from "./config";

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
                            <Route default path="/" component={Timers} apiRootUrl={BACKEND_API_ROOT} />
                            <Route path="/logs" component={Logs} apiRootUrl={BACKEND_API_ROOT} />
                            <Route path="/stats" component={Stats} apiRootUrl={BACKEND_API_ROOT} />
                            <Route path="/reset" component={Reset} apiRootUrl={BACKEND_API_ROOT} />
                            <Route default component={NotFound} />
                        </Router>
                    </main>
                </Sheet>
            </CssVarsProvider>
        </LocationProvider>
    );
}

render(<App />, document.getElementById("app"));
