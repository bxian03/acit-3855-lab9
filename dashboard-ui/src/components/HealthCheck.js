import React, { useEffect, useState } from 'react'
import '../App.css';

export default function HealthCheck(props) {
    const [isLoaded, setIsLoaded] = useState(false);
    const [log, setLog] = useState(null);
    const [error, setError] = useState(null)
	// const rand_val = Math.floor(Math.random() * 100); // Get a random event from the event store
    const [index] = useState(null)

    // Get current seconds
    const date_now = new Date();

    // Get seconds from json data
    const date_before = new Date(log['last_updated']);
    const date_dif = ((date_now.getTime() - date_before.getTime()) / 1000);

    const getAudit = () => {
        fetch(`http://acit-3855-docker.eastus.cloudapp.azure.com/${props.endpoint}`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Health Results for " + props.endpoint)
                setLog(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
	useEffect(() => {
		const interval = setInterval(() => getAudit(), 4000); // Update every 4 seconds
		return() => clearInterval(interval);
    }, [getAudit]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        
        return (
            <div>
                <h3>{props.endpoint}</h3>
                {/* {JSON.stringify(log)} */}
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<td colSpan="2">receiver: {log['receiver']}</td>
						</tr>
						<tr>
							<td colSpan="2">storage: {log['storage']}</td>
						</tr>
						<tr>
							<td colSpan="2">processing: {log['processing']}</td>
						</tr>
                        <tr>
                            <td colSpan="2">audit: {log['audit']}</td>
                        </tr>
                        <tr>
                            <td colSpan="2">last updated: {date_dif} seconds ago</td>
                        </tr>
					</tbody>
                </table>
            </div>
        )
    }
}
