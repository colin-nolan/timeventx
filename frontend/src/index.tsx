import { render } from "preact";
import { LocationProvider, Router, Route } from "preact-iso";

import { Header } from "./components/Header";
import { Home } from "./pages/Home";
import { NotFound } from "./pages/_404";
import "./style.css";
import React from "react";
import { JoyToaster } from "./components/JoyToaster";
import { Logs } from "./pages/Logs";
import { Stats } from "./pages/Stats";
import { Reset } from "./pages/Reset";

// TODO: configure
const API_ROOT = "http://192.168.0.156:8080/api/v1";
// const API_ROOT = "http://0.0.0.0:8080/api/v1";

export function App() {
    return (
        <LocationProvider>
            <JoyToaster />
            <Header />
            <main style={{ marginTop: "20px" }}>
                <Router>
                    <Route path="/" component={Home} apiRootUrl={API_ROOT} />
                    <Route path="/logs" component={Logs} apiRootUrl={API_ROOT} />
                    <Route path="/stats" component={Stats} apiRootUrl={API_ROOT} />
                    <Route path="/reset" component={Reset} apiRootUrl={API_ROOT} />
                    <Route default component={NotFound} />
                </Router>
            </main>
        </LocationProvider>
    );
}

render(<App />, document.getElementById("app"));
