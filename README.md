# simulated-city-template

## Template for a project

### Step 1: Define Your Simulation (Before Any Code)
“Up to 30 cars drive on the Copenhagen road network. When selected road segments are blocked due to roadwork, affected cars reroute to alternative paths, and congestion emerges on detour roads.

### My Smart City Project: [Project Name]
Roadwork

#### 1. The Trigger (Who/What is moving?)
Agents: Up to 30 generic car agents moving from origin to destination on the Copenhagen road network.
Surroundings: Road segment status (open/blocked), simulation time (ticks), and optional traffic density on nearby roads.
Trigger event: A roadwork event blocks selected road segments, so affected cars must reroute.

#### 2. The Observer (What does the city see?)
Sensors/inputs:

A roadwork status source marks selected Copenhagen road segments as blocked or open.
Car agents report their current segment and speed each tick.
What the city observes:

Which road segments are currently blocked
How many cars are on each nearby segment
Whether average speed drops on detour roads (congestion signal)
Observer output:

A live traffic state showing blocked roads, car flow, and emerging congestion hotspots.

#### 3. The Control Center (The Logic)
The city processes roadwork and traffic updates each tick and applies simple routing rules:

If a car’s planned route contains a blocked road segment, the car recalculates a new route that avoids blocked segments.
If multiple valid routes exist, the car selects the one with lowest current cost (for example shortest travel time or least congestion).
If no route is available, the car enters a temporary waiting state and retries after a short cooldown.
The system flags congestion when car density is high or average speed drops below a threshold on detour roads.
Control output:
Reroute decisions and congestion status updates are published so other agents and the dashboard can react.

#### 4. The Response (What happens next?)
Controller: The car-routing controller in each car agent changes behavior based on roadwork events.

When a road segment is blocked, affected cars switch to a new route that avoids blocked segments.
Cars update their speed/position on the new path and publish reroute status.
The traffic state changes on the map: flow shifts to detour roads, and congestion can build there.
When roadwork ends, new routes can include the reopened segment again.
City change produced by the controller: route updates, shifted traffic patterns, and congestion hotspots on alternative roads.
