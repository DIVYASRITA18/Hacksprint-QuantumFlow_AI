<<<<<<< HEAD
# QuantumFlow — Live Microscopic Traffic Simulation

This version replaces the previous static road-line visualization with a browser-side microscopic simulation.

## What is simulated
- Cars, buses and trucks move continuously on two lanes.
- Vehicles stop behind red signals and form visible queues.
- Each intersection has N/S and E/W signal states that automatically adapt to queue pressure.
- Green approaches release queued vehicles and traffic visibly moves through the intersection.
- Ambulance dispatch creates a moving green corridor on I1 → I2 → I3 → I6.
- Conflicting approaches turn red while the emergency corridor is active.
- Vehicles in the emergency approach are released while the ambulance advances from junction to junction.
- After the ambulance clears the route, adaptive signal control resumes.
- The simulation has Start, Pause, Reset and Dispatch Ambulance controls.

## Run

```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

Open **Live Traffic Simulation** and press **Start**. Press **Dispatch Ambulance** to demonstrate the emergency green corridor.


IMPORTANT: The live vehicle simulation is in the Live Traffic Simulation tab. It is a canvas animation, not the static Traffic Network map. Cars, buses, trucks and the ambulance are drawn as moving vehicle bodies.
=======
# Hacksprint
>>>>>>> 7b8885ce726913cc4ab1a76f3fd97881e392bf56
