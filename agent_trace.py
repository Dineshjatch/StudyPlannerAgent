
from datetime import datetime

trace = []

def log(step, details):
    trace.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "step": step,
        "details": details
    })

def show_trace():
    return trace