import dash
from dash import dcc, html
import plotly.graph_objs as go
import random
import time

# Initialize Dash
app = dash.Dash(__name__)

# Global lists to store simulated data
times = []
altitudes = []
speeds = []
rocket_states = ["Idle", "Boost", "Apogee", "Drogue", "Main", "Landed"]

# Simulate some initial data for testing
start_time = time.time()
for i in range(20):
    current_time = time.time() - start_time
    altitude = random.uniform(0, 100)
    speed = random.uniform(0, 50)
    times.append(current_time)
    altitudes.append(altitude)
    speeds.append(speed)
    time.sleep(0.1)

# Layout of the Dashboard
app.layout = html.Div([
    # Background video
    html.Video(
        src="/assets/rocket.mp4",
        autoPlay=True,
        loop=True,
        muted=True,
        style={
            'position': 'fixed',
            'top': '50%',
            'left': '50%',
            'transform': 'translate(-50%, -50%)',
            'min-width': '100%',
            'min-height': '100%',
            'width': 'auto',
            'height': 'auto',
            'z-index': '-1',
            'object-fit': 'cover'
        }
    ),

    # Vertical timeline and progress bar
html.Div([
    # Text Labels
    html.Div([
        html.Div("INIT", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("IDLE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("BOOST", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("APOGEE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("DROGUE", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("MAIN", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'}),
        html.Div("LANDED", style={'color': 'white', 'writing-mode': 'vertical-rl', 'text-orientation': 'upright'})
    ], style={
        'position': 'absolute', 'top': '4%', 'left': '10px',
        'height': '80%', 'display': 'flex', 'flex-direction': 'column',
        'justify-content': 'space-between', 'align-items': 'center',
        'font-size': '12px', 'font-weight': 'bold'
    }),

    # Progress Bar (Shifted right)
    html.Div([
        html.Div(id="progress-bar", style={
            'width': '10px', 'height': '10%', 'background-color': 'white',
            'transition': 'height 0.5s ease-in-out'
        })
    ], style={
        'width': '10px', 'height': '100%', 'display': 'flex', 'align-items': 'flex-end',
        'border': '2px solid white',
        'margin-left': '30px'  # Adjusted for spacing
    })
    ], style={
        'position': 'absolute', 'top': '4%', 'left': '10px', 'height': '80%',
        'display': 'flex', 'flex-direction': 'row', 'align-items': 'center'
    }),

    # Bottom telemetry data
    html.Div([
        html.Div([
            html.Div("CAPSULE VELOCITY", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='speed', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'}),
        html.Div([
            html.Div("CAPSULE ALTITUDE", style={'color': 'white', 'font-size': '14px'}),
            html.H3(id='altitude', style={'color': 'white'})
        ], style={'text-align': 'center', 'padding': '0 20px'})
    ], style={
        'position': 'absolute', 'bottom': '20px', 'left': '240px',
        'transform': 'translateX(-50%)', 'display': 'flex',
        'gap': '50px', 'background': 'rgba(0, 0, 0, 0.1)',
        'padding': '5px 20px', 'border-radius': '10px', 
    }),

    # Mission time
    html.Div([
        html.H1("T+ 00:00:02", id='mission-time')
    ], style={
        'position': 'absolute', 'bottom': '20px', 'right': '20px',
        'background': 'rgba(0, 0, 0, 0.1)', 'padding': '10px 20px',
        'border-radius': '10px', 'color': 'white'
    }),

    # Logo
    html.Img(src="/assets/seds.png", style={'position': 'absolute', 'top': '10px', 'right': '10px', 'width': '100px', 'opacity' : '0.5'}),

    # Interval component for real-time updates
    dcc.Interval(id='interval-component', interval=1000, n_intervals=0)
])

# Callback for updating progress bar
@app.callback(
    dash.dependencies.Output('progress-bar', 'style'),
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_progress(n):
    stage_progress = {
        "Idle": 100, "Boost": 85, "Apogee": 68, "Drogue": 51, "Main": 34, "Landed": 17
    }
    current_stage = random.choice(list(stage_progress.keys()))

    return {
        'width': '10px', 'height': f"{stage_progress[current_stage]}%",
        'background-color': 'white', 'transition': 'height 0.5s ease-in-out'
    }

# Callback for updating telemetry data
@app.callback(
    [
        dash.dependencies.Output('altitude', 'children'),
        dash.dependencies.Output('speed', 'children'),
        dash.dependencies.Output('mission-time', 'children')
    ],
    [dash.dependencies.Input('interval-component', 'n_intervals')]
)
def update_data(n):
    current_time = time.time() - start_time
    new_altitude = random.uniform(0, 100)
    new_speed = random.uniform(0, 50)
    elapsed_time = f"T+ {int(current_time // 60):02}:{int(current_time % 60):02}:{int((current_time % 1) * 100):02}"

    times.append(current_time)
    altitudes.append(new_altitude)
    speeds.append(new_speed)

    return f"{new_speed:.0f} MPH", f"{new_altitude:.0f} FT", elapsed_time

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=False)
    
