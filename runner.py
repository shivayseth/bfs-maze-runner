#runner.py
#Handles runner creation and primitive movements:
#The runner is represented as a small dictionary for simplicity.
def create_runner(x: int = 0, y: int =0, orientation: str='N'):
    #create and return a runner represented as a simple dict
    return {'x':x,'y':y,'orientation':orientation}

def get_x(runner):
    #return x coordinate of runner
    return runner['x']
def get_y(runner):
    #return y coordinate of runner
    return runner['y']
def get_orientation(runner):
     #returns the direction the runner is facing
    return runner['orientation']
def turn(runner, direction: str):
    #changes orientation without changing position
    orientations=['N','E','S','W']
    current= orientations.index(runner['orientation'])
    #left = -1 step, right = +1 step
    if direction=='Left':
        new_orientation= orientations[(current-1)%4]
    elif direction == 'Right':
        new_orientation = orientations[(current + 1) % 4]
    else:
        raise ValueError #invalid direction

    #return new runner dict with updated orientation
    return {'x': runner['x'], 'y': runner['y'], 'orientation': new_orientation}
def forward(runner):
    #move one step forward based on orientation
    x = runner['x']
    y=runner['y']
    orientation = runner["orientation"]
    if orientation == 'N':
        y+=1
    elif orientation =='S':
        y-=1
    elif orientation =='E':
        x+=1
    elif orientation =='W':
        x-=1
    #return new runner position
    return {"x": x, "y": y, "orientation": orientation}