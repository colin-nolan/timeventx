import preactLogo from '../../assets/preact.svg';
import './style.css';
import {useState} from "preact/compat";


const API_ROOT = "http://localhost:8080/api/v1"

interface DayTime {
	hour: number;
	minute: number;
	second: number;
}

interface Timer {
	name: string;
	start_time: DayTime;
	duration_in_seconds: number
}


export function Home() {
	const [timers, setTimers] = useState<Timer[]>([
		{
			"name": "test",
			"start_time": {
				"hour": 0,
				"minute": 0,
				"second": 0
			},
			"duration_in_seconds": 10
		}
	]);

	const fetchUserData = () => {
		console.log("fetching")
		fetch(`${API_ROOT}/timers`)
			.then(response => {
				console.log(response)
				return response.json()
			})
	}
	fetchUserData()
	console.log(fetchUserData)

	return (
		<>
			<div>Hello world x{timers.length}</div>

			{timers.map((timer) => (
				<div>{timer.name}</div>
			))}
		</>
	);
}
