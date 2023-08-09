import './style.css';
import {useEffect, useState} from "preact/compat";


const API_ROOT = "http://192.168.0.156:8080/api/v1"
// const API_ROOT = "http://0.0.0.0:8080/api/v1"

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

	const [name, setName] = useState<string>("");
	const [startTime, setStartTime] = useState<string>("00:00:00")
	const [durationInSeconds, setDurationInSeconds] = useState<number>(0)

	function add_timer() {
		// TODO@ handle not enough separator
		// const [hours, minutes, seconds] = startTime.split(":")

		fetch(`${API_ROOT}/timer`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json"
			},
			body: JSON.stringify({
				name: name,
				start_time: startTime,
				duration: durationInSeconds
			})
		})
			.then(async (response) => {
				const timer = await response.json()
				setTimers([...timers, timer])
			})
	}


	useEffect(() => {
		fetch(`${API_ROOT}/timers`)
			.then(async (response) => {
				const timers = await response.json()
				setTimers(timers)
			})
	}, []);

	return (
		<>
			<div>Hello world x{timers.length}</div>

			<div>
				{timers.map((timer) => (
					<div>{timer.name}</div>
				))}
			</div>
			<div>
				Name: <input type="text" onChange={event => setName(event.target.value)} value={name}/><br/>
				Start Time: <input type="string" onChange={event => setStartTime(event.target.value)} value={startTime}/><br/>
				Duration: <input type="number" onChange={event => setDurationInSeconds(event.target.value)} value={durationInSeconds}/><br/>
				<button onClick={() => {add_timer()}}>Add</button>
			</div>
		</>
	);
}
