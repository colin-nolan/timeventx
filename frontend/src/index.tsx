import { render } from "preact";
import { LocationProvider, Router, Route } from "preact-iso";

import { Header } from "./components/Header";
import { Home } from "./pages/Home";
import { NotFound } from "./pages/_404";
import "./style.css";
import React from "react";
import { JoyToaster } from "./components/JoyToaster";

export function App() {
    return (
        <LocationProvider>
            <JoyToaster />
            <Header />
            <main style={{ marginTop: "20px" }}>
                <Router>
                    <Route path="/" component={Home} />
                    <Route default component={NotFound} />
                </Router>
            </main>
        </LocationProvider>
    );
}

render(<App />, document.getElementById("app"));
