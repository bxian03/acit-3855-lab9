import React, { useEffect, useState } from 'react'
import '../App.css';

export default function AppStats() {
    const [isLoaded, setIsLoaded] = useState(false);
    const [stats, setStats] = useState({});
    const [error, setError] = useState(null)

	const getStats = () => {
	
        fetch(`http://acit-3855-docker.eastus.cloudapp.azure.com/processing/stats`)
            .then(res => res.json())
            .then((result)=>{
				console.log("Received Stats")
                setStats(result);
                setIsLoaded(true);
            },(error) =>{
                setError(error)
                setIsLoaded(true);
            })
    }
    useEffect(() => {
		const interval = setInterval(() => getStats(), 2000); // Update every 2 seconds
		return() => clearInterval(interval);
    }, [getStats]);

    if (error){
        return (<div className={"error"}>Error found when fetching from API</div>)
    } else if (isLoaded === false){
        return(<div>Loading...</div>)
    } else if (isLoaded === true){
        return(
            <div>
                <h1>Latest Stats</h1>
                <table className={"StatsTable"}>
					<tbody>
						<tr>
							<td># order_count: {stats['order_count']}</td>
                            <td># pizza_count: {stats['pizza_count']}</td>
						</tr>
						<tr>
							<td colSpan="2">order_mean_cost: {stats['order_mean_cost']}</td>
						</tr>
						<tr>
							<td colSpan="2">order_mean_quantity: {stats['order_mean_quantity']}</td>
						</tr>
						<tr>
							<td colSpan="2">pizza_mean_cost: {stats['pizza_mean_cost']}</td>
						</tr>
                        <tr>
                            <td colSpan="2">pizza_mean_quantity: {stats['pizza_mean_quantity']}</td>
                        </tr>
					</tbody>
                </table>
                <h3>Last Updated: {stats['last_updated']}</h3>

            </div>
        )
    }
}
