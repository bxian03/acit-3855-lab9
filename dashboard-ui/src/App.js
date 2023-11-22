import logo from './logo.png';
import './App.css';

import EndpointAudit from './components/EndpointAudit'
import AppStats from './components/AppStats'
import HealthCheck from './components/HealthCheck';

function App() {

    const endpoints = ["/audit_log/pizza_order", "audit_log/driver_order"]

    const rendered_endpoints = endpoints.map((endpoint) => {
        return <EndpointAudit key={endpoint} endpoint={endpoint}/>
    })

    const health = ["/health/"]

    const rendered_health = <HealthCheck key={health} endpoint={health}/>

    return (
        <div className="App">
            <img src={logo} className="App-logo" alt="logo" height="150px" width="400px"/>
            <div>
                <AppStats/>
                <h1>Audit Endpoints</h1>
                {rendered_endpoints}
                <h1>Health Check</h1>
                {rendered_health}
            </div>
        </div>
    );

}



export default App;
