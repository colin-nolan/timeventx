import { render } from 'preact';
import { LocationProvider, Router, Route } from 'preact-iso';

import { Header } from './components/Header';
import { Home } from './pages/Home';
import { NotFound } from './pages/_404';
import './style.css';
import Testing from "./pages/Testing";

export function App() {
	return (
		<LocationProvider>
			<Header />
			<main style={{marginTop: "20px"}}>
				<Router>
					<Route path="/" component={Home} />
					<Route path="/testing" component={Testing} />
					<Route default component={NotFound} />
				</Router>
			</main>
		</LocationProvider>
	);
}

render(<App />, document.getElementById('app'));
